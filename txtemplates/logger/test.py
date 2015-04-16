import os
import sys
import logging
import logging.config

BASEDIR = os.path.realpath(os.path.dirname(os.path.dirname(sys.path[0])))
logdir = os.path.join(BASEDIR, 'logs')
OUTFILE = os.path.join(logdir, 'tests.log')
if not os.path.exists(logdir):
    os.mkdir(logdir)

TEST_LOGGING = {
    'version': 1,
    'incremental': False,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'testfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'mode': 'a',
            'filename': OUTFILE,
        },
    },
    'loggers': {
        'test_output': {
            'level': 'INFO',
            'propagate': True,
            'filters': [],
            'handlers': ['testfile']
        },
    },
}


def configure_logger():
    logging.config.dictConfig(TEST_LOGGING)
    return logging.getLogger('test_output')
