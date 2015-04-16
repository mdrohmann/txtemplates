import collections
from functools import wraps

import pytest

from twisted.python import log
from twisted.internet import defer
from twisted.internet.defer import maybeDeferred
from twisted.spread import jelly


def jelly_test(value):
    try:
        a = jelly.jelly(value)
        nvalue = jelly.unjelly(a)
        assert nvalue == value
    except Exception as e:
        pytest.fail("Error trying to jelly {}: {}".format(value, e))


def merge_options(opt_obj, options, name='Unknown'):
    config = opt_obj
    keys = config.keys()
    config.update(options)
    nkeys = config.keys()
    diff = set(nkeys) - set(keys) - set(opt_obj.subkeys)
    if len(diff) > 0:
        raise ValueError(
            'Unknown keys in configuration of {} found: {}.\n'
            'Maybe you need to add "subkeys" to the Option class.'
            .format(name, ', '.join(diff)))
    config.postOptions()
    return config


def getSecureSession(request, sessionInterface=None):
    """
    This creates a secure session cookie, that is supposed to only be sent over
    secure connections.
    """

    # Session management
    if not request.isSecure():
        return None

    if not request.session:
        cookiename = b"_".join([b'TWISTED_SESSION'] + request.sitepath)
        sessionCookie = request.getCookie(cookiename)
        if sessionCookie:
            try:
                request.session = request.site.getSession(sessionCookie)
            except KeyError:
                pass
        # if it still hasn't been set, fix it up.
        if not request.session:
            request.session = request.site.makeSession()
            request.addCookie(
                cookiename, request.session.uid, path=b'/', secure=True)
    request.session.touch()
    if sessionInterface:
        return request.session.getComponent(sessionInterface)
    return request.session


def parallel_generator(iterator, parallelity, func, *args, **kwargs):
    """
    generates parallel jobs and waits for them to complete.

    This generator starts a set of jobs in parallel (defined by
    :args:`parallelity`) and waits for ALL of them to complete before
    processing further jobs.

    .. todo::

        Use cooperative tasks to always hold a queue of parallelity jobs open.
    """
    cache = []
    for i in iterator:
        d = defer.maybeDeferred(func, i, *args, **kwargs)
        cache.append(d)
        if len(cache) == parallelity:
            gd = defer.gatherResults(cache)
            cache = []
            yield gd

    if len(cache) > 0:
        yield defer.gatherResults(cache)


class CachedQueue(object):
    """
    This queue adds elements to a cache before they are processed, and after
    processing copies them in a queue for fast access of the last results.

    When a deferred object processes this cache as an argument, it needs to
    trigger the function :meth:`arg_processed` afterwards.
    """

    def __init__(self, processor, maxlen=100, max_cachelen=100):
        self.max_cachelen = max_cachelen
        self.__queue = collections.deque([], maxlen)
        self.__cache = collections.deque([])
        self.__processor = processor
        self.init_d()

    def cb_pre_arg_processed(self, ignored):
        self.d = None
        return defer.succeed(self.__cache)

    def init_d(self):
        self.d = defer.Deferred()
        self.d.addCallback(self.cb_pre_arg_processed)
        self.d.addCallback(self.__processor)
        self.d.addCallbacks(self.cb_arg_processed, self.log_errs)

    def log_errs(self, failure):
        log.err(failure)
        log.err('Items {} could not be processed in CachedQueue'.format(
            repr(self.__cache)))
        return None

    def get_queue(self):
        return self.__queue

    def get_arg(self):
        return self.__cache

    def cb_arg_processed(self, number=None):
        self.init_d()
        if number is None or len(self.__cache) == number:
            number = len(self.__cache)
            self.__queue.extend(self.__cache)
            self.__cache.clear()
        else:
            self.__queue.extend(
                [self.__cache.popleft() for i in range(number)])
        if len(self.__cache) > 0:
            self.d.callback(None)
        return defer.succeed(number)

    def add_item(self, item):
        if len(self.__cache) + 1 > self.max_cachelen:
            log.err(
                'Overfull CachedQueue! Dropped item: {}'.format(repr(item)))
            raise RuntimeError(
                'CachedQueue is overfull.'
                'Check if consumer is still running.')
        self.__cache.append(item)
        if self.d is not None:
            self.d.callback(None)


def deferred_wrapper(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        return maybeDeferred(f, *args, **kwds)
    return wrapper


# vim: set spell spelllang=en sw=4:
