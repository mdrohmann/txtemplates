import json
from cgi import escape as _e
from twisted.web import resource, server
from twisted.python import components

from txtemplates.echo.service import IService

from ...utils.html import (
    BadRequestError, BadRequestJsonError, best_fitting_mimetype)


class Echo(resource.Resource):

    isLeaf = True
    allowedMethods = ['GET', 'POST']

    def __init__(self, service):
        resource.Resource.__init__(self)
        self.service = service
        self._render_GET_mime = {
            'text/html': self._render_GET_html,
            'application/json': self._render_GET_json,
        }

    def _cb_echo_html_received(self, text, request):
        request.setHeader("content-type", "text/html; charset=utf-8")
        request.write(
            "<html><body><h1>Received text</h1><p>{}</p></body></html>"
            .format(text))
        request.finish()

    def _cb_echo_json_received(self, text, request):
        request.setHeader("content-type", "application/json; charset=utf-8")
        request.write(json.dumps({'return': text}))
        request.finish()

    def render(self, request):

        mimefunction = best_fitting_mimetype(request, self._render_GET_mime)

        return mimefunction(request)

    def _render_GET_json(self, request):
        try:
            args = json.load(request.content)
        except Exception as e:
            return BadRequestJsonError(
                "Error reading arguments: {}".format(e)).render(request)

        if 'value' in args:
            content = _e(str(args['value']))
        else:
            return BadRequestJsonError(
                "Required 'value' field missing.").render(request)

        d = self.service.echo(content)
        d.addCallback(self._cb_echo_json_received, request)

        return server.NOT_DONE_YET

    def _render_GET_html(self, request):
        args = request.args
        if 'value' in args:
            content = _e(' '.join(args['value']))
        else:
            return BadRequestError(
                "Required 'value' field missing.").render(request)

        d = self.service.echo(content)
        d.addCallback(self._cb_echo_html_received, request)

        return server.NOT_DONE_YET


class EchoRoot(resource.Resource):

    isLeaf = False

    def __init__(self, service):
        resource.Resource.__init__(self)
        self.service = service

    def getChild(self, name, request):
        if name == 'echo':
            return Echo(self.service)
        else:
            return resource.NoResource()


def registerAdapters():
    try:
        components.registerAdapter(
            EchoRoot,
            IService,
            resource.IResource)
    except ValueError:
        pass

# vim: set ft=python sw=4 et spell spelllang=en:
