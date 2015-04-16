from zope.interface import Interface, implements

from twisted.spread import pb
from twisted.python import components

from ...utils.zope_ext import get_methods_for_interface
from ..service import IService


class IPerspective(Interface):

    def remote_echo(text):
        """
        returns a deferred returning text
        """


class PerspectiveFromService(pb.Root):
    implements(IPerspective)

    def __init__(self, service):
        self.s = service
        for method in get_methods_for_interface(IPerspective, 'remote_'):
            setattr(self, method, getattr(self.s, method[7:]))


def registerAdapters():
    try:
        components.registerAdapter(
            PerspectiveFromService,
            IService,
            IPerspective)
    except ValueError:
        pass

# vim: set ft=python sw=4 et spell spelllang=en:
