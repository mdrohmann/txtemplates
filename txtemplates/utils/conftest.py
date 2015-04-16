# encoding: utf-8

"""
File: conftest.py
Author: Martin C. Drohmann
Email: mdrohmann@gmail.com
Github: https://github.com/mdrohmann
Description: pytest configuration file with standard tests for server modules.
"""

import re
import copy

import pytest
import numpy as np
from twisted.application import service
from twisted.python.reflect import namedAny
from twisted.spread import pb
from twisted.internet import reactor, defer
from twisted.web import resource, server, client
from zope.interface.verify import verifyObject

from txtemplates.common import backend
from txtemplates.utils.zope_ext import (
    create_dummy_class_for, get_methods_for_interface)
from txtemplates.utils.html import SingleWebRequest


@pytest.fixture(scope="module")
def html_request(request):
    return copy.copy(request.param)


@pytest.fixture(scope="module")
def backend_options(request):
    return copy.copy(request.param)


@pytest.fixture(scope="module")
def full_server_options(request):
    return copy.copy(request.param)


@pytest.fixture(scope="class")
def backend_methods_fixture(request):
    return copy.copy(request.param)


def _make_backend(boptions, module):

    np.random.seed(323)
    if boptions == 'dummy':
        DummyBackend = create_dummy_class_for(module.backend.IBackend)
        return DummyBackend()
    else:
        return module.backend.make_backend(boptions)


@pytest.fixture()
def backend_fixture(backend_options):
    options = backend_options[0]
    module = backend_options[1]
    try:
        return _make_backend(options, module), module
    except Exception, e:
        return e, module


#@pytest.fixture()
#def dummy_backend_fixture(request):
#    server_module = request.param
#    DummyBackend = create_dummy_class_for(server_module.backend.IBackend)
#    d = DummyBackend()
#    verifyObject(server_module.backend.IBackend, d)
#    return d
#
#

@pytest.fixture(scope="class")
def service_fixture(full_server_options):

    [boptions, soptions], module = full_server_options

    try:
        db = _make_backend(boptions, module)
    except Exception, e:
        return e, module
    try:
        ret = module.service.decorate_backend(db, soptions)
    except Exception as e:
        ret = e
    return ret, module


def _guard_test(module):
    try:
        module.registerAdapters()
    except ValueError:
        pytest.fail(
            "Please guard the registerAdapters function in {}"
            .format(str(module)))


@pytest.fixture(scope="class")
def pb_adapter_fixture(service_fixture):
    ds = service_fixture[0]
    module = service_fixture[1]

    module.protocol.pb.registerAdapters()
    _guard_test(module.protocol.pb)
    pfs = module.protocol.pb.IPerspective(ds)
    return pfs, module


@pytest.fixture(scope="class")
def web_adapter_fixture(service_fixture):
    ds = service_fixture[0]
    module = service_fixture[1]

    module.protocol.html.registerAdapters()
    _guard_test(module.protocol.html)
    res = resource.IResource(ds)
    return res, module


@pytest.fixture(scope="class")
def full_pb_server(request, pb_adapter_fixture):

    pfs, module = pb_adapter_fixture

    try:
        factory = pb.PBServerFactory(pfs)
        ret = reactor.listenTCP(0, factory)

        def fin():
            ret.stopListening()

        request.addfinalizer(fin)

    except Exception as e:
        return e, module

    return ret, module


@pytest.fixture(scope="class")
def full_web_server(request, web_adapter_fixture):

    res, module = web_adapter_fixture

    try:
        site = server.Site(res)
        ret = reactor.listenTCP(0, site)

        def fin():
            ret.stopListening()

        request.addfinalizer(fin)

    except Exception as e:
        return e, module

    return ret, module


@pytest.fixture(scope="class")
def pb_proxy(request, full_pb_server):
    server, module = full_pb_server
    port = server.getHost().port
    interface = module.backend.IBackend
    pbproxy = backend.PbProxy(
        interface, 'tcp:localhost:port={}:timeout=3'.format(port), reactor)

    def fin():
        pbproxy.root_object.broker.transport.loseConnection()

    request.addfinalizer(fin)
    pytest.blockon(pbproxy.connection)
    pytest.blockon(pbproxy.d)
    return pbproxy, module


def _get_options_ids_and_module(
        scope, config, servers_name, var_lists, server_name):

    opname = var_lists[0]
    idname = var_lists[1]
    if hasattr(scope, servers_name):
        config.update(getattr(scope, servers_name))
    else:
        if hasattr(scope, server_name):
            server_name = getattr(scope, server_name)
        else:
            server_name = config.keys()[0]

        tmp = {}
        if hasattr(scope, opname):
            tmp[opname] = getattr(scope, opname)

        if hasattr(scope, idname):
            tmp[idname] = getattr(scope, idname)
        elif idname not in config.get(server_name, {}):
            tmp[idname] = None

        if not server_name in config:
            config[server_name] = {}

        config[server_name].update(tmp)

    return config


def _check_options_ids_and_module(config, names):
    if len(config) == 0:
        raise ValueError("Failed to configure options, ids and modules.")
    for c in config.itervalues():
        for name in names:
            if name not in c:
                raise ValueError(
                    "Missing configuration value {}!".format(name))


def get_options_ids_and_module(metafunc, name):
    """
    retrieves two variables from the nearest available scope around the
    function called.

    The variables, we are searching for, have the names

      - `{name}_options` and
      - `{name}_ids`
      - `server_module`

    The 'class' and 'module' scopes are searched for these variable names.

    Alternatively, `server_modules` variable.  This variable must be a
    dictionary, where the keys are module names, and the values should be
    dictionaries with keys `{name}_options` and `{name}_ids`.

    An example for this configuration is:

    .. code:: python

      server_modules = {
          'voteapp.echo': {
              'backend_options': [{}], 'backend_ids': ['default'] },
          'voteapp.tallygist': {
              'backend_options': [{}], 'backend_ids': ['default'] },
      }

    The return value has the above form.
    """

    option_name = '{}_options'.format(name)
    id_name = '{}_ids'.format(name)

    names = [option_name, id_name]
    server_module_name = 'server_module'.format(name)
    server_modules_name = 'server_modules'.format(name)

    config = {}
    try:
        package = metafunc.module.__package__
        confmodule = namedAny(package).conftest
        config = _get_options_ids_and_module(
            confmodule, config, server_modules_name, names, server_module_name)
    except:
        pass
    try:
        config = _get_options_ids_and_module(
            metafunc.cls, config, server_modules_name, names,
            server_module_name)
    except:
        pass

    _check_options_ids_and_module(config, names)

    return _get_options(config, names)


def _get_options(option_config, names):
    opret = []
    idsret = []
    for (k, v) in option_config.iteritems():
        module = namedAny(k)
        opts = v[names[0]]
        ids = v[names[1]]
        opret += zip(opts, [module for _ in enumerate(opts)])
        if ids is None:
            idsret = None
        else:
            if idsret is None:
                raise ValueError(
                    "Ids need to be None for all or none of the test modules.")
            else:
                idsret += ids
                assert len(idsret) == len(opret)

    return opret, idsret


def _get_backend_options(metafunc):
    params, ids = get_options_ids_and_module(metafunc, 'backend')
    return params, ids


def _get_full_server_options(metafunc):
    params, ids = get_options_ids_and_module(metafunc, 'full_server')
    return params, ids


def get_server_module(metafunc):
    try:
        server_module_name = namedAny(
            metafunc.module.__package__).conftest.server_module
    except:
        pass
    if metafunc.cls is not None and hasattr(metafunc.cls, 'server_module'):
        server_module_name = metafunc.cls.server_module
    return namedAny(server_module_name)


def pytest_generate_tests(metafunc):
    if 'backend_fixture' in metafunc.fixturenames:
        params, ids = _get_backend_options(metafunc)
        metafunc.parametrize('backend_options', params, ids=ids, indirect=True)

    if 'service_fixture' in metafunc.fixturenames:
        params, ids = _get_full_server_options(metafunc)
        metafunc.parametrize(
            'full_server_options', params, ids=ids, indirect=True,
            scope="class")

    if 'backend_methods_fixture' in metafunc.fixturenames:
        module = get_server_module(metafunc)
        methods = get_methods_for_interface(module.backend.IBackend)
        if hasattr(metafunc.cls, 'xfail_methods'):
            xfail_methods = metafunc.cls.xfail_methods
            methods = [
                pytest.mark.xfail(m, run=False)
                if m in xfail_methods else m
                for m in methods]
        metafunc.parametrize('backend_methods_fixture', methods, indirect=True)

    if 'html_request' in metafunc.fixturenames:
        if hasattr(metafunc.cls, 'webrequests'):
            ids = []
            opts = metafunc.cls.webrequests
            for i, wr in enumerate(opts):
                if not isinstance(wr, SingleWebRequest):
                    pytest.fail(
                        "webrequests attribute needs to be a list of "
                        "'SingleWebRequest' objects")
                if wr.id:
                    ids.append(wr.id)
                else:
                    ids.append('wr-{}'.format(i+1))
        metafunc.parametrize('html_request', opts, indirect=True, ids=ids)


def cb_error(failure):
    print failure
    assert 0


class WorkingServiceBase(object):

    def test_service(self, service_fixture):
        ds, module = service_fixture
        verifyObject(module.service.IService, ds)
        assert isinstance(ds, service.Service)


class DummyServiceBase(object):
    full_server_options = [('dummy', {})]
    full_server_ids = ['dummy_service']

    def test_methods_return_deferreds(self, service_fixture):
        ds, module = service_fixture
        for method in get_methods_for_interface(module.service.IService):
            op = getattr(ds, method)
            ret = op()
            assert isinstance(ret, defer.Deferred)


class FailingServiceBase():
    full_server_options = [('dummy', {'unknown': 'parameter'})]
    full_server_ids = ['too_many_parameters']

    def test_service_error(self, service_fixture):
        service, _ = service_fixture
        assert isinstance(service, ValueError)
        assert 'Unknown keys' in service.message


class WorkingBackendsBase(object):

    def test_backend(self, backend_fixture):
        b, module = backend_fixture
        assert verifyObject(module.backend.IBackend, b)


class FailingBackendsBase(object):

    backend_options = [{'unknown': 'parameter'}]
    backend_ids = ['too_many_parameters']

    def test_backend_error(self, backend_fixture):
        backend, _ = backend_fixture
        assert isinstance(backend, ValueError)
        assert 'Unknown keys' in backend.message


class PBAdapterBase(object):

    def test_pb_adaptation(self, pb_adapter_fixture):
        pfs, module = pb_adapter_fixture
        assert isinstance(pfs, module.protocol.pb.PerspectiveFromService)

        verifyObject(module.protocol.pb.IPerspective, pfs)


class PBDummyServerBase(object):
    full_server_options = [('dummy', {})]
    full_server_ids = ['dummy']

    def test_pb_echo(self, pb_proxy, backend_methods_fixture):
        proxy, module = pb_proxy
        verifyObject(module.backend.IBackend, proxy)
        o = getattr(proxy, backend_methods_fixture)
        d = o()
        assert isinstance(d, defer.Deferred)

        def cb_check_return(ret):
            assert ret.startswith(
                'Called {} successfully'.format(backend_methods_fixture))

        d.addCallbacks(cb_check_return, cb_error)

        return d


class WebResourcesBase(object):

    def test_real_webrequests(self, html_request, service_fixture,
                              full_web_server, monkeypatch):

        service, _ = service_fixture
        html_request.mock(service, monkeypatch)
        server, module = full_web_server

        port = server.getHost().port

        d = html_request.realRender(port)

        def cb_body_received(body, wr):
            if 'body' in wr.expect:
                assert re.search(wr.expect['body'], body)

        def cb_rendered(response, wr):
            if 'code' in wr.expect:
                assert response.code == wr.expect['code']

            d = client.readBody(response)
            d.addCallback(cb_body_received, wr)
            return d

        d.addCallback(cb_rendered, html_request)
        return d

# vim: set ft=python sw=4 et spell spelllang=en:
