from zope.interface import implements
from zope.interface.verify import verifyObject
from twisted.application import service
from twisted.python import usage

from .backend import IBackend
from ..utils.zope_ext import copy_interface
from ..utils.twisted_ext import merge_options


class IService(IBackend):
    pass


class ServiceFromBackend(service.Service):
    """
    makes a service from an IBackend.

    .. todo::

        Use Mixins to create more functionality for this service, like
        repetitive logging of Tallygist health.
    """
    implements(IService)

    def __init__(self, backend):
        self.backend = backend
        copy_interface(self, IBackend, backend, wrap_deferred=True)


class Options(usage.Options):
    optParameters = []

    optFlags = []

    subkeys = []


def decorate_backend(backend, options={}):
    config = Options()
    config.parseOptions('')
    config = merge_options(config, options, 'Echo service decorator')
    service = ServiceFromBackend(backend)
    verifyObject(IBackend, service)
    verifyObject(IService, service)
    return service

# vim: set ft=python spell spelllang=en sw=4 et:
