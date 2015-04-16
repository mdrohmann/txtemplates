import json
import itertools
import mimetools
import mimetypes
from StringIO import StringIO

from twisted.web._responses import BAD_REQUEST, NOT_IMPLEMENTED
from twisted.web import resource, client
from twisted.web.http_headers import Headers
from twisted.internet import reactor


class JsonErrorPage(resource.ErrorPage):

    def __init__(self, code, description, message):
        resource.ErrorPage.__init__(self, code, description, message)

    def render(self, request):
        request.setResponseCode(self.code)
        request.setHeader(b"content-type", b"application/json; charset=utf-8")
        interpolated = json.dumps({
            'error_code': self.code,
            'brief': self.brief,
            'detail': self.detail
            })
        return interpolated


class BadRequestJsonError(JsonErrorPage):

    def __init__(self, message="Bad request error"):
        JsonErrorPage.__init__(
            self, BAD_REQUEST, "Bad request", message)


class BadRequestError(resource.ErrorPage):

    def __init__(self, message="Bad request error"):
        resource.ErrorPage.__init__(
            self, BAD_REQUEST, "Bad request", message)


class NotImplementedErrorPage(resource.ErrorPage):

    def __init__(self, message="method not implemented"):
        resource.ErrorPage.__init__(
            self, NOT_IMPLEMENTED, "Not implemented", message)


class SingleWebRequest(object):

    def __init__(
            self, path,
            mock_functions=[], accept_headers=[],
            body=None, method='GET', id=None, expect={}):
        self.path = path
        self.mock_functions = mock_functions
        self.accept_headers = accept_headers
        self.body, self.contenttype = self._get_body_producer(body)
        self.method = method
        self.id = id
        self.expect = expect

    def mock(self, service, monkey):
        for m in self.mock_functions:
            monkey.setattr(service, m['method'], m['patch'])

    def _get_body_producer(self, body_text):
        if type(body_text) is dict:
            if (not 'content-type' in body_text
                    or body_text['content-type'] == 'multipart/form'):
                mpf = MultiPartForm()
                if 'files' in body_text:
                    files = body_text.pop('files')
                    for f in files:
                        mimetype = None
                        if 'mimetype' in f:
                            mimetype = f['mimetype']
                        mpf.add_file(
                            f['name'], f['fname'], f['handle'], mimetype)
                for (k, v) in body_text.iteritems():
                    mpf.add_field(k, v)
                res = str(mpf)
                ct = mpf.get_content_type()
            else:
                res = body_text['value']
                ct = body_text['content-type']

            return (client.FileBodyProducer(StringIO(res)), ct)
        else:
            return None, None

    def realRender(self, port):
        agent = client.Agent(reactor)

        headers = Headers({
            'User-Agent': ['Twisted Web Client']})
        for aheader in self.accept_headers:
            headers.addRawHeader('Accept', aheader)

        if self.body is not None:
            headers.addRawHeader('Content-type', self.contenttype)

        d = agent.request(
            self.method,
            'http://localhost:{}/{}'.format(port, self.path),
            headers,
            bodyProducer=self.body)

        def _cb_agent_error(failure):
            print failure
            import pudb
            pudb.set_trace()

        d.addErrback(_cb_agent_error)

        return d


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(
                filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached
        files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [part_boundary,
             'Content-Disposition: form-data; name="{}"'.format(name),
             '',
             str(value)]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [part_boundary,
             'Content-Disposition: file; name="{}"; filename="{}"'
             .format(field_name, filename),
             'Content-Type: {}'.format(content_type),
             '',
             body]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


# if __name__ == '__main__':
#     from cStringIO import StringIO
#     import urllib2
#     # Create the form with simple fields
#     form = MultiPartForm()
#     form.add_field('firstname', 'Doug')
#     form.add_field('lastname', 'Hellmann')
#
#     # Add a fake file
#     form.add_file('biography', 'bio.txt',
#                   fileHandle=StringIO('Python developer and blogger.'))
#
#     # Build the request
#     request = urllib2.Request('http://localhost:8080/')
#     request.add_header(
#         'User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
#     body = str(form)
#     request.add_header('Content-type', form.get_content_type())
#     request.add_header('Content-length', len(body))
#     request.add_data(body)
#
#     print
#     print 'OUTGOING DATA:'
#     print request.get_data()


def accepted_mimetypes(request, default='text/html'):
    """ returns the accepted mimetypes of an HTTP/1.1 request

    It returns a dictionary of the accepted mimetypes as
    keys and their priorities as values.
    """
    accepted_strings = request.requestHeaders.getRawHeaders(
        'Accept', [default])
    accepted_strings = ','.join(accepted_strings)
    splits = [a.split(';q=') for a in accepted_strings.split(',')]
    return dict(
        [(a[0].strip().lower(), len(a) == 2 and float(a[1]) or 1)
         for a in splits])


def best_fitting_mimetype(request, mimetype_dict, default='text/html'):
    accepted_strings = accepted_mimetypes(request)

    sas = sorted(
        accepted_strings.iteritems(), key=lambda x: x[1], reverse=True)
    for mt in sas:
        if mt[0] in mimetype_dict:
            return mimetype_dict[mt[0]]

    return NotImplementedErrorPage(
        "No implementation for accepted mimetypes available.").render

# vim: set ft=python sw=4 et spell spelllang=en:
