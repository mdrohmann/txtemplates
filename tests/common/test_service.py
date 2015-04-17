import pytest
import json

from twisted.python import usage
from twisted.application import service

import txtemplates.common.service as vcs


def test_options_errors():
    """
    tests the errors in the Options class for the service configuration.
    """

    config = vcs.Options()

    with pytest.raises(usage.UsageError) as excinfo:
        config.parseOptions('')

    assert 'at least one address' in str(excinfo.value)

    config = vcs.Options()

    with pytest.raises(usage.UsageError) as excinfo:
        config.parseOptions('-A address1 -A address2 -P pb'.split(' '))

    assert '2 != 1' in str(excinfo.value)


def test_options():
    """
    tests Options class for the service configuration.
    """

    config = vcs.Options()

    config.parseOptions(
        '-A address1 -A address2 -c configfile.json'.split(' '))

    assert len(config['addresses']) == 2
    assert len(config['protocols']) == 2
    assert config['config'] == 'configfile.json'


scenarios = [
    ('echo', 'txtemplates.echo', 'Echo debug test', 'echo'),
    #    ('tallygist', 'voteapp.tallygist', 'tallygist test', 'tallygist'),
    ]
ids = ['echo'  # , 'tallygist'
       ]


@pytest.fixture(params=scenarios, ids=ids)
def servicemaker(request):
    sm = vcs.ServiceMaker(*request.param)
    return sm


class TestServiceMaker:

    def test_init(self, servicemaker, request):
        assert servicemaker.name is not None

    def test_empty_options(self, servicemaker):
        config = servicemaker.get_empty_options()

        assert 'addresses' in config

    def test_make_service(self, servicemaker):
        config = servicemaker.options()
        config.parseOptions('-A unix:test.socket'.split(' '))

        s = servicemaker.makeService(config)
        assert isinstance(s, service.MultiService)

    @pytest.mark.parametrize(
        'inopts,length,protocols',
        [
            ({'addresses': ['unix:test.socket'], 'protocols': ['html']},
             1, ['html']),
            ({'addresses': ['unix:test.socket']}, 1, ['pb']),
        ])
    def test_read_config_file(
            self, servicemaker, tmpdir, inopts, length, protocols):

        c = tmpdir.join("test.json")
        with open(str(c), 'w') as fh:
            json.dump(inopts, fh)

        config = servicemaker.get_empty_options()
        config['config'] = str(c)
        options = servicemaker._read_config_file(config)
        assert len(options['addresses']) == length
        assert len(options['protocols']) == length
        assert options['protocols'] == protocols

    @pytest.mark.parametrize(
        'inopts,error',
        [
            ({'addresses': ['unix:test.socket', 'unix:test2.socket'],
              'protocols': ['html']},
             usage.UsageError),
            ({}, usage.UsageError),
            (None, ValueError),
        ])
    def test_read_config_file_error_1(
            self, servicemaker, tmpdir, inopts, error):

        c = tmpdir.join("test.json")
        with open(str(c), 'w') as fh:
            if inopts is None:
                fh.write('{"invalid": "json",}')
            else:
                json.dump(inopts, fh)

        config = servicemaker.get_empty_options()
        config['config'] = str(c)
        with pytest.raises(error):
            servicemaker._read_config_file(config)

    def test_read_config_file_error_2(
            self, servicemaker, tmpdir):

        tmpdir.chdir()

        config = servicemaker.get_empty_options()
        config['config'] = 'invalid.json'
        with pytest.raises(RuntimeError) as excinfo:
            servicemaker._read_config_file(config)

        assert 'Could not open configfile invalid.json' in str(excinfo)

# vim: set ft=python sw=4 et spell spelllang=en
