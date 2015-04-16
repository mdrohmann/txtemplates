# encoding: utf-8

import os
import argparse
import sys
import re
import importlib
import pytest
from voteapp import server_templates
import voteapp


def test_get_parser_error(capsys):
    parser = server_templates.get_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])

    _, err = capsys.readouterr()
    assert re.search('error: too few arguments', err)


@pytest.mark.parametrize('argstr, expected', [
    ('module', {'name': 'module', 'module': 'voteapp'}),
    ('module package', {'name': 'module', 'module': 'package'}),
    ('module package -C directory', {'directory': 'directory'})
    ])
def test_get_parser(argstr, expected):
    parser = server_templates.get_parser()
    args = parser.parse_args(argstr.split(' '))
    for (k, v) in expected.items():
        assert hasattr(args, k)
        assert getattr(args, k) == v


def test_get_target_module():
    directory = os.path.dirname(os.path.dirname(voteapp.__file__))
    args = argparse.Namespace(module='voteapp', directory=directory)
    module = server_templates.get_target_module(args)
    assert module == voteapp
    args = argparse.Namespace(module='voteapp', directory='/tmp')
    module = server_templates.get_target_module(args)
    assert module == voteapp


@pytest.fixture(scope="function")
def testpackage(tmpdir):
    p = tmpdir.mkdir("testpackage").join("__init__.py")
    p.write("")
    args = argparse.Namespace(module='testpackage', directory=str(tmpdir))
    package = server_templates.get_target_module(args)
    return tmpdir, package


def test_dirs(testpackage):
    tempdir, package = testpackage
    basedir = str(tempdir)
    parser = server_templates.get_parser()
    args = parser.parse_args('module testpackage'.split(' '))
    dirs = server_templates.Dirs(args, package)
    assert dirs.module == os.path.join(basedir, 'testpackage', 'module')
    assert dirs.twistedplugin == os.path.join(
        basedir, 'testpackage', 'twisted', 'plugins')
    assert dirs.testbase == os.path.join(basedir, 'tests')
    assert dirs.test == os.path.join(basedir, 'tests', 'module')


def test_run(testpackage, monkeypatch):
    tempdir, package = testpackage
    monkeypatch.setattr(
        sys, "argv",
        "main.py testmodule testpackage -C {}"
        .format(str(tempdir)).split(" "))

    server_templates.main()

    files = [str(f)[len(str(tempdir)):] for f in tempdir.visit()]
    assert len(files) == 22
    assert '/testpackage/testmodule/backend/__init__.py' in files
    assert '/tests/testmodule/test_testmodule_backend.py' in files

# vim:set ft=python sw=4 et spell spelllang=en:
