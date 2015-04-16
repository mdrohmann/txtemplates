"""
TODO: Make this a test somehow.

"""


from pprint import pformat

from twisted.internet import reactor, task, defer
from twisted.internet.ssl import PrivateCertificate, ClientContextFactory
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.web.resource import Resource
from twisted.web import client
from twisted.web.http_headers import Headers
from twisted.internet.endpoints import TCP4ServerEndpoint
from voteapp.utils.twisted_ext import getSecureSession

from twisted.web.server import Site

with open("/home/martin/workspace/twisted/docs/core/examples/server.pem") as f:
    cert = PrivateCertificate.loadPEM(f.read())


class CountingResource(Resource):
    """
    A resource that counts.
    """
    isLeaf = True

    def render_GET(self, request):
        """
        Render a GET.
        """
        session = getSecureSession(request)
        from_text = 'insecure connection'
        if request.isSecure():
            from_text = 'secure connection'
        headers = b'Request headers from {}:'.format(from_text)
        headers += pformat(list(request.requestHeaders.getAllRawHeaders()))
        if session:
            session.value = getattr(session, "value", 0) + 1
            request.setHeader("content-type", "text/plain")
            return (
                b"counter: " + unicode(session.value).encode("ascii")
                + "\n" + headers)
        else:
            return b"counter: unknown" + "\n" + headers


site = Site(CountingResource())
secureEndpoint = SSL4ServerEndpoint(reactor, 8443, cert.options())
secureEndpoint.listen(site)
insecureEndpoint = TCP4ServerEndpoint(reactor, 8081)
insecureEndpoint.listen(site)


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


def cbResponse(response, from_text):
    print 'Response headers from {}:'.format(from_text)
    print pformat(list(response.headers.getAllRawHeaders()))
    d = client.readBody(response)
    d.addCallback(cbBody, from_text)
    return d


def cbBody(body, from_text):
    print 'Response body from {}:'.format(from_text)
    print body


def cbStop(ignored):
    reactor.stop()


contextFactory = WebClientContextFactory()


def insecure_request():
    http_agent = client.Agent(reactor)
    d = http_agent.request(
        'GET',
        'http://localhost:8081/',
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        None)
    d.addCallback(cbResponse, 'insecure connection')
    return d


def secure_request():
    https_agent = client.Agent(reactor, contextFactory)
    d = https_agent.request(
        'GET',
        'https://localhost:8443/',
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        None)
    d.addCallback(cbResponse, 'secure connection')
    return d


d1 = task.deferLater(reactor, 3, secure_request)
d2 = task.deferLater(reactor, 4, secure_request)
d3 = task.deferLater(reactor, 5, insecure_request)
d4 = task.deferLater(reactor, 6, secure_request)

ds = defer.gatherResults([d1, d2, d3, d4])
ds.addCallbacks(cbStop, cbStop)

reactor.run()
