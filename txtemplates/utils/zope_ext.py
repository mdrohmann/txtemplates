import zope
from .twisted_ext import deferred_wrapper


def _get_zope_types(interface, classtype, startswith, recursive=True):
    types = [m[0] for m in interface.namesAndDescriptions()
             if (type(m[1]) == classtype and m[0].startswith(startswith))]
    if recursive:
        for base in interface.getBases():
            types += _get_zope_types(base, classtype, startswith)
    return types


def get_methods_for_interface(interface, startswith='', recursive=True):
    return _get_zope_types(
        interface, zope.interface.interface.Method, startswith, recursive)


def get_attributes_for_interface(interface, startswith='', recursive=True):
    return _get_zope_types(
        interface, zope.interface.interface.Attribute, startswith, recursive)


def _emptyreturn(f):
    def wrapper(*args, **kwds):
        return "Called {} successfully".format(f)
    return wrapper


def create_dummy_class_for(interface):

    class _DummyBackend:
        zope.interface.implements(interface)

        def __init__(self):
            for method in get_methods_for_interface(interface):
                setattr(self, method, _emptyreturn(method))
            for attribute in get_attributes_for_interface(interface):
                setattr(self, attribute, attribute)

    return _DummyBackend


def copy_interface(obj, interface, cpy, wrap_deferred=False):
    """
    copies interface methods from cpy into obj.
    """

    for method in get_methods_for_interface(interface):
        newfun = getattr(cpy, method)
        if wrap_deferred:
            newfun = deferred_wrapper(newfun)

        setattr(obj, method, newfun)
    for attribute in get_attributes_for_interface(interface):
        setattr(obj, attribute, getattr(cpy, attribute))


# vim: set ft=python sw=4 et spell spelllang=en:
