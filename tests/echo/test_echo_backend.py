from ..conftest import WorkingBackendsBase, FailingBackendsBase

"""
The minimal tests for the backend should test the make_backend function and the
implementation functionality.

"""


class TestWorkingBackends(WorkingBackendsBase):

    def test_echo(self, backend_fixture):
        b, _ = backend_fixture

        assert b.echo('test') == 'test'


class TestBackendErrors(FailingBackendsBase):
    pass


# vim: set ft=python sw=4 et spell spelllang=en:
