import os
import sys
import logging
import logging.config

BASEDIR = os.path.realpath(os.path.dirname(sys.path[0]))
OUTFILE = os.path.join(BASEDIR, 'out.log')

DEFAULT_LOGGING = {
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
        'outfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'mode': 'a',
            'filename': OUTFILE,
        },
    },
    'loggers': {
        'default_output': {
            'level': 'INFO',
            'propagate': True,
            'filters': [],
            'handlers': ['outfile']
        },
    },
}


def configure_logger():
    logging.config.dictConfig(DEFAULT_LOGGING)
    return logging.getLogger('default_output')
