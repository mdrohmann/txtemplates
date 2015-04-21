# encoding: utf-8

import pytest
from txtemplates.dist import Version, IncomparableVersions


@pytest.mark.parametrize(
    'version,sexpected,lexpected,sversion',
    [
        (Version('test', 1, 0, 2), '1.0', '1.0.2', '[test, version 1.0.2]'),
        (Version('package', 10, 2, 3, 'devel'),
         '10.2', '10.2.3-devel', '[package, version 10.2.3-devel]'),
    ])
def test_strings(version, sexpected, lexpected, sversion):

    assert version.long() == lexpected
    assert version.short() == sexpected
    assert str(version) == sversion
    assert repr(version) == sversion


@pytest.mark.parametrize(
    'version_small,version_big',
    [
        (Version('test', 1, 10, 20), Version('test', 2, 0, 0)),
        (Version('test', 1, 10, 20), Version('test', 1, 20, 0)),
        (Version('test', 1, 10, 20, 'devel'), Version('test', 1, 10, 20)),
        (Version('test', 1, 10, 19), Version('test', 1, 10, 20, 'devel')),
        (Version('test', 1, 10, 19, 'devel'),
         Version('test', 1, 10, 20, 'devel')),
    ])
def test_less_compare(version_small, version_big):
    assert version_small < version_big


@pytest.mark.parametrize(
    'version1,version2',
    [
        (Version('test', 1, 10, 20), Version('test', 1, 10, 20)),
        (Version('test', 1, 10, 20, 'devel'),
         Version('test', 1, 10, 20, 'devel')),
        (Version('test', 1, 10, 20, 'devel'),
         Version('test', 1, 10, 20, 'alpha')),
    ])
def test_equal_compare(version1, version2):
    assert version1 == version2


@pytest.mark.parametrize(
    'version1,version2,error',
    [
        (Version('test', 0, 1, 0), '0.1.0', NotImplementedError),
        (Version('test', 0, 1, 0), Version('test2', 0, 1, 0), IncomparableVersions),
    ])
def test_compare_error(version1, version2, error):
    with pytest.raises(error):
        version1 == version2

# vim:set ft=python sw=4 et spell spelllang=en:
