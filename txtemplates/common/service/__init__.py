"""
Common tools for services.

A service should provide a function makeService(options) and a class Options
derived from twisted.python.usage.Options.  It creates services for protocol /
backend combinations.
"""
import json

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.python.reflect import namedAny
from twisted.python import usage
from twisted.application import service, strports
from twisted.spread import pb

from ...utils.twisted_ext import merge_options


class Options(usage.Options):
    optParameters = [['config', 'c', None, 'Configuration file']]

    def __init__(self):
        usage.Options.__init__(self)
        self['addresses'] = []
        self['protocols'] = []

    def opt_protocol(self, protocol):
        """
        Define the protocol to use with a listening address.
        """
        self['protocols'].append(protocol)

    def opt_address(self, address):
        """
        Define an address to listen on.
        """
        self['addresses'].append(address)

    opt_P = opt_protocol
    opt_A = opt_address

    compData = usage.Completions(
        optActions={"config": usage.CompleteFiles("*.json"),
                    "address": usage.CompleteNetInterfaces()}
        )

    def postOptions(self):
        if len(self['addresses']) == 0:
            raise usage.UsageError("You need to specify at least one address!")
        if len(self['protocols']) == 0:
            self['protocols'] = [
                'pb' for _ in enumerate(self['addresses'])]

        if len(self['protocols']) != len(self['addresses']):
            raise usage.UsageError(
                "Mismatch between number of addresses and protocols: {} != {}"
                .format(len(self['addresses']), len(self['protocols'])))
        return self

    subkeys = ['service']


class ServiceMaker(object):
    """
    Utility class to simplify the definition of a twistd plugin.
    """
    implements([IPlugin, IServiceMaker])

    def __init__(self, name, module, description, tapname):
        self.name = name
        self.module = module
        self.description = description
        self.tapname = tapname
        self.protocol_factory_makers = {'pb': self.make_pb_factory}
        Options.subkeys.append(tapname)

    options = Options

    def make_pb_factory(self, backend_service):

        pbmodule = namedAny(self.module).protocol.pb
        # register adapters
        pbmodule.registerAdapters()
        # create the IPerspective
        perspective = pbmodule.IPerspective(backend_service)
        # create the factory
        factory = pb.PBServerFactory(perspective)
        return factory

    def _make_backend():
        def get(self):
            return namedAny(self.module).backend.make_backend
        return get,
    make_backend = property(*_make_backend())

    def _decorate_backend():
        def get(self):
            return namedAny(self.module).service.decorate_backend
        return get,
    decorate_backend = property(*_decorate_backend())

    def get_empty_options(self):
        """
        returns empty options which is useful, in case the ServiceMaker is not
        called as a plugin.
        """

        config = self.options()
        return config

    def _read_config_file(self, options):
        if options['config'] is not None:
            try:
                with open(options['config'], 'r') as fh:
                    configfile_options = json.load(fh)
            except IOError:
                raise RuntimeError(
                    "Could not open configfile {}".format(options['config']))
            except ValueError as e:
                raise ValueError(
                    "JSON error in configfile {}:\n{}"
                    .format(options['config'], e.message))
            options = merge_options(
                options, configfile_options,
                '{} (configfile: {}'.format(self.name, options['config']))

        return options

    def _get_backend(self, options):
        backend_options = options.get(self.name, {})
        return self.make_backend(backend_options)

    def _decorate_backend(self, backend, options):
        service_options = options.get('service', {})
        return self.decorate_backend(backend, service_options)

    def _make_factory(self, protocol, backend_service):
        return self.protocol_factory_makers[protocol](backend_service)

    def makeService(self, config):
        s = service.MultiService()

        options = self.get_empty_options()
        options.update(config)
        self._read_config_file(options)

        backend = self._get_backend(options)

        backend_service = self._decorate_backend(backend, options)
        backend_service.setServiceParent(s)

        protocol_dict = dict([(p, []) for p in set(options['protocols'])])
        for p, a in zip(options['protocols'], options['addresses']):
            protocol_dict[p].append(a)

        for protocol, addresses in protocol_dict.iteritems():
            factory = self._make_factory(
                protocol, backend_service)

            for address in addresses:
                server = strports.service(address, factory)
                server.setServiceParent(s)

        return s

# vim: set ft=python sw=4 et spell spelllang=en:
