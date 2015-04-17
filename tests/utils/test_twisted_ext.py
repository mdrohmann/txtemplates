import pytest
import StringIO
from txtemplates.utils.twisted_ext import (
    CachedQueue, parallel_generator, jelly_test)
from twisted.internet import defer, task
from twisted.python import log


def test_jelly_test():
    class Unjellyable:
        pass

    a = Unjellyable()
    with pytest.raises(Exception):
        jelly_test(a)


@pytest.mark.parametrize('parallelity,length', [(1, 3), (2, 2), (4, 1)])
def test_cached_generator(parallelity, length):

    def simple_fun(k):
        return defer.succeed(k)

    res = [d for d in parallel_generator([1, 2, 3], parallelity, simple_fun)]
    assert len(res) == length
    assert all([isinstance(d, defer.Deferred) for d in res])


def dummycachequeue(processing_limit, processor_raises_error=False):
    clock = task.Clock()

    def error_callback(ignored):
        raise RuntimeError("something went wrong")

    def processor(cache):
        d = defer.Deferred()
        clock.callLater(10, d.callback, (processing_limit))
        if processor_raises_error:
            d.addCallback(error_callback)
        return d

    cq = CachedQueue(processor, 5, 10)

    return cq, clock


def test_cached_queue1():
    cq, clock = dummycachequeue(10)

    for item in range(10):
        cq.add_item(item)

    assert list(cq.get_arg()) == range(10)
    assert len(cq.get_queue()) == 0
    clock.advance(10)
    assert list(cq.get_queue()) == range(5, 10)
    assert len(cq.get_arg()) == 0


def test_cached_queue2():
    cq, clock = dummycachequeue(5)

    for item in range(10):
        cq.add_item(item)
    # process 5 items only
    clock.advance(10)
    assert list(cq.get_queue()) == range(5)
    assert list(cq.get_arg()) == range(5, 10)
    # process all items
    clock.advance(10)
    assert list(cq.get_queue()) == range(5, 10)
    assert len(cq.get_arg()) == 0


def test_cached_queue3():
    cq, clock = dummycachequeue(10)

    # add too many items
    with pytest.raises(RuntimeError):
        for item in range(11):
            cq.add_item(item)


def test_cached_queue_log_err():
    logoutput = StringIO.StringIO()
    log.startLogging(logoutput)
    cq, clock = dummycachequeue(10, processor_raises_error=True)

    cq.add_item([1])
    clock.advance(10)

    assert logoutput.getvalue().find("something went wrong") > 0


# vim: set spell spelllang=en sw=4:
