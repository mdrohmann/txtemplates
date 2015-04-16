from zope.interface import Interface, implements
from twisted.python import usage
from ...utils.twisted_ext import merge_options
from ...common.backend import PbProxy, ProxyOptions


class IBackend(Interface):

    def echo(text):
        """
        returns the text
        """


class ServerOptions(usage.Options):
    optParameters = []

    optFlags = []

    subkeys = []


class Options(usage.Options):
    subCommands = [
        ['server', None, ServerOptions, 'create a default server'],
        ['proxy', None, ProxyOptions, 'create a backend proxy'],
    ]


class EchoBackend(object):
    implements(IBackend)

    def echo(self, text):
        return text


def make_proxy_backend(boptions):
    pbproxy = PbProxy(IBackend, boptions['address'])
    return pbproxy


def make_backend(options):
    config = Options()
    command = 'server'
    if 'command' in options:
        command = options.pop('command')

    config.parseOptions([command])
    config = config.subOptions
    config = merge_options(config, options, 'Echo backend')

    if command == 'server':
        backend = EchoBackend()
        return backend
    elif command == 'proxy':
        return make_proxy_backend(config)

# vim: set ft=python sw=4 et spell spelllang=en:
