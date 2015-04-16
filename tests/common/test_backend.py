from twisted.internet import defer, reactor
from voteapp.common import backend
import voteapp.echo


def test_pb_proxy_failed():
    interface = voteapp.echo.backend.IBackend
    pbproxy = backend.PbProxy(
        interface, 'tcp:localhost:port=1234:timeout=1', reactor)

    def cb_connection_error(failure):
        assert isinstance(failure.type(), RuntimeError)

    pbproxy.connection.addErrback(cb_connection_error)

    return pbproxy.connection


def cb_error(failure):
    print failure
    assert 0


def test_pb_echo_2(pb_proxy):
    proxy, _ = pb_proxy
    message = 'hi'
    message2 = 'welt'
    d = proxy.echo(message)
    d2 = proxy.echo(message2)
    assert isinstance(d, defer.Deferred)

    def cb_check_return(ret):
        assert ret == message

    def cb_check_return2(ret):
        assert ret == message2

    d.addCallbacks(cb_check_return, cb_error)
    d2.addCallbacks(cb_check_return2, cb_error)
    gd = defer.gatherResults([d, d2])
    return gd


# vim: set ft=python sw=4 et spell spelllang=en:
