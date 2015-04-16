"""
Collection of certain backends and their interfaces.

Every backend should provide a make_service() function, that creates the
service, and an IBackend Interface class, that defines the backend interface.
"""

import zope

from twisted.spread import pb
from twisted.python import usage
from twisted.internet import endpoints, reactor, defer
from twisted.spread.pb import DeadReferenceError

from ...utils.zope_ext import (
    get_methods_for_interface, get_attributes_for_interface)


class ProxyOptions(usage.Options):
    optParameters = [
        ['address', 'A', '', 'proxy address', str]
    ]

    subkeys = []


def _proxy_call(inst, method):

    def wrapper(*args, **kwargs):

        def wrapper2(_):
            d = inst.root_object.callRemote(method, *args, **kwargs)
            d.addErrback(inst.failed_call_try_fix)
            d.addErrback(inst.failed_call_report, method, *args, **kwargs)
            return d

        if inst.root_object is None:
            d = defer.Deferred()
            d.addCallback(wrapper2)
            inst.d.chainDeferred(d)
            return d
        else:
            return wrapper2(None)

    return wrapper


class PbProxy(object):

    def __new__(cls, interface, *args, **kwargs):
        zope.interface.classImplements(cls, interface)
        inst = object.__new__(cls)
        for method in get_methods_for_interface(interface):
            proxy_call = _proxy_call(inst, method)
            setattr(inst, method, proxy_call)
        for attribute in get_attributes_for_interface(interface):
            setattr(inst, attribute, None)
        return inst

    def __init__(self, interface, address, reactor=reactor):
        self.reactor = reactor
        self.root_object = None
        self.factory = pb.PBClientFactory()
        self.connection = self.init_connection(address)
        self.init_root_object()

    def init_root_object(self):
        self.init_called = True
        self.d = self.factory.getRootObject().addCallbacks(
            self.cb_gotRoot, self.cb_notGotRoot)

    def failed_call_try_fix(self, failure):
        r = failure.trap(DeadReferenceError)
        if r == DeadReferenceError:
            self.root_object = None
            self.d = self.factory.getRootObject().addCallbacks(
                self.cb_gotRoot, self.cb_notGotRoot)

    def failed_call_report(self, failure, method, *args, **kwargs):
        print (
            "Call to {} with args: {} failed, because of: \n{}"
            .format(method, repr(args) + repr(kwargs), failure))

    def cb_gotRoot(self, root):
        self.root_object = root
        return None

    def cb_notGotRoot(self, failure):
        raise RuntimeError(
            "Could not receive root object from server:\n{}".format(failure))

    def cb_connection_failed(self, failure):
        raise RuntimeError(
            "Connection from Proxy to Server failed:\n{}".format(failure))

    def init_connection(self, address):
        unixend = endpoints.clientFromString(
            self.reactor, address)
        conn = unixend.connect(self.factory)
        conn.addErrback(self.cb_connection_failed)
        return conn

# vim: set ft=python sw=4 et spell spelllang=en:
