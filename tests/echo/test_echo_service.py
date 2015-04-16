from ..conftest import WorkingServiceBase, FailingServiceBase, DummyServiceBase


class TestService(WorkingServiceBase):
    pass


class TestServiceErrors(FailingServiceBase):
    pass


class TestDummyService(DummyServiceBase):
    pass

# vim: set ft=python sw=4 et spell spelllang=en:
