"""
Common methods for backend loggers.
"""

from datetime import datetime
import json


def force_close(fh):
    try:
        fh.close()
    except:
        pass


def get_timestamp():
    return datetime.now().strftime('%Y%m%d-%H%M')


def fh_write(fh, blob):
    line = json.dumps(blob)
    fh.write(line + '\n')

# vim: set ft=python spell spelllang=en sw=4 et:
