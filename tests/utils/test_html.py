#!/usr/bin/env python
# encoding: utf-8

import re
from StringIO import StringIO
import pytest
from voteapp.utils.html import (
    accepted_mimetypes, SingleWebRequest, BadRequestError)
from twisted.web.test import requesthelper

from voteapp.logger import test

logger = test.configure_logger()


def test_json_error_page(dummyrequest):
    bre = BadRequestError(message=u'blöde nachricht mit Ümläuten.')
    res = bre.render(dummyrequest)
    assert type(res) is str and type(res) is not unicode


def test_webrequest_files():
    wr = SingleWebRequest('/')
    p, mime = wr._get_body_producer(
        {'files': [{
            'name': 'the_file',
            'fname': 'file.txt',
            'handle': StringIO('This is a test')
            }, {
            'name': 'other_file',
            'fname': 'file2.txt',
            'handle': StringIO('This is another test'),
            'mimetype': 'application/text'
            }]})
    assert re.search('multipart/form', mime)
    from twisted.test.proto_helpers import StringTransport
    s = StringTransport()
    g = p._writeloop(s)
    [_ for _ in g]
    assert re.search('This is a test', s.value())
    assert re.search('This is another test', s.value())
    assert re.search('application/text', s.value())


@pytest.fixture()
def dummyrequest():
    return requesthelper.DummyRequest([])


def test_accepted_mimetypes_default(dummyrequest):
    assert accepted_mimetypes(dummyrequest) == {'text/html': 1}


def test_accepted_mimetypes_1(dummyrequest):
    dummyrequest.requestHeaders.addRawHeader('Accept', 'a')

    assert accepted_mimetypes(dummyrequest) == {'a': 1}


def test_accepted_mimetypes_2(dummyrequest):
    dummyrequest.requestHeaders.addRawHeader('Accept', 'a')
    dummyrequest.requestHeaders.addRawHeader('Accept', 'b')

    assert accepted_mimetypes(dummyrequest) == {'a': 1, 'b': 1}


def test_accepted_mimetypes_3(dummyrequest):
    dummyrequest.requestHeaders.addRawHeader('Accept', 'a')
    dummyrequest.requestHeaders.addRawHeader('Accept', 'b;q=0.5')

    assert accepted_mimetypes(dummyrequest) == {'a': 1, 'b': 0.5}


def test_accepted_mimetypes_4(dummyrequest):
    dummyrequest.requestHeaders.addRawHeader('Accept', 'a,c;q=0.3   , D  ')
    dummyrequest.requestHeaders.addRawHeader('Accept', 'b;q=0.5')

    assert accepted_mimetypes(dummyrequest) == {
        'a': 1, 'b': 0.5, 'c': 0.3, 'd': 1}

# vim: set spell spelllang=en sw=4:
