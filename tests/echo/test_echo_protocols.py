import json

from twisted.internet import defer
import twisted.web._responses as RESPONSE

from ..conftest import (PBDummyServerBase, PBAdapterBase, WebResourcesBase)
from voteapp.utils.html import SingleWebRequest


class TestPBAdapter(PBAdapterBase):
    pass


class TestDummyServer(PBDummyServerBase):
    """
    if any of the methods of your backend interface are not working in the
    ProxyBackend, mark them as xfail_methods here.
    """
    xfail_methods = []


class TestWithEchoService(WebResourcesBase):
    full_server_options = [('dummy', {})]
    full_server_ids = ['dummy']

    def dummy_echo(res):
        return defer.succeed(res)

    monkey_patch = [{'method': 'echo', 'patch': dummy_echo}]

    webrequests = [
        SingleWebRequest(
            '/',
            method='GET', id='root_not_found',
            expect={
                'code': RESPONSE.NOT_FOUND,
            }),
        SingleWebRequest(
            'echo',
            method='HEAD', id='HEAD_not_allowed',
            expect={
                'code': RESPONSE.BAD_REQUEST,
            }),
        SingleWebRequest(
            'echo',
            method='GET', id='get_missing_value',
            expect={
                'code': RESPONSE.BAD_REQUEST,
                'body': "Required 'value' field missing"
            }),
        SingleWebRequest(
            'echo?value=12',
            method='GET', id='simple_get',
            expect={
                'code': RESPONSE.OK,
                'body': "Called echo successfully"
            }),
        SingleWebRequest(
            'echo?value=12',
            method='GET', id='get_patched',
            mock_functions=monkey_patch,
            expect={
                'code': RESPONSE.OK,
                'body': "<p>12</p>"
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='post_missing_value',
            expect={
                'code': RESPONSE.BAD_REQUEST,
                'body': "Required 'value' field missing"
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='post_success',
            body={'value': 13},
            mock_functions=monkey_patch,
            expect={
                'code': RESPONSE.OK,
                'body': "<p>13</p>"
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='post_json_no_json',
            accept_headers=['application/json'],
            expect={
                'code': RESPONSE.BAD_REQUEST,
                'body': "No JSON object could be decoded"
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='post_json_missing_value',
            body={
                'content-type': 'application/json',
                'value': json.dumps({'useless': 14})},
            accept_headers=['application/json'],
            expect={
                'code': RESPONSE.BAD_REQUEST,
                'body': "Required \\'value\\' field missing"
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='post_json',
            accept_headers=['application/json'],
            body={
                'content-type': 'application/json',
                'value': json.dumps({'value': 14})},
            mock_functions=monkey_patch,
            expect={
                'code': RESPONSE.OK,
                'body': json.dumps({'return': '14'})
            }),
        SingleWebRequest(
            'echo',
            method='POST', id='not_implemented',
            accept_headers=['text/csv'],
            mock_functions=monkey_patch,
            expect={
                'code': RESPONSE.NOT_IMPLEMENTED,
                'body': 'No implementation for accepted mimetypes available'
            }),
    ]

# vim: set ft=python sw=4 et spell spelllang=en:
