# encoding: utf-8

import os
import argparse
import imp
import importlib
from jinja2 import Environment, FileSystemLoader


def silent_mkdirs(path):
    try:
        os.makedirs(path)
    except:
        pass


class Dirs(object):

    def __init__(self, args, target_module):
        basedir = os.path.dirname(target_module.__file__)
        self.module = os.path.join(basedir, args.name)
        self.twistedplugin = os.path.join(basedir, 'twisted', 'plugins')
        self.testbase = os.path.join(os.path.dirname(basedir), 'tests')
        self.test = os.path.join(self.testbase, args.name)
        silent_mkdirs(self.module)
        silent_mkdirs(self.test)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', metavar='NAME', type=str,
        help='name of the server module')
    parser.add_argument(
        'module', metavar='MODULE', type=str, nargs='?',
        default='txtemplates',
        help='name of the base module')
    parser.add_argument(
        '-C', '--directory', metavar='DIRECTORY', type=str,
        default='.',
        help='change in this directory before creating the files')
    parser.add_argument(
        '-f', '--force-overwrite', action='store_true',
        help='overwrite existing files')
    return parser


def prepare_templates(args):
    loader = FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates'))
    env = Environment(loader=loader)

    values = {'name': args.name, 'module': args.module}
    templates = loader.list_templates()
    return env, templates, values


def get_target_module(args):
    f = None
    try:
        (f, pathname, desc) = imp.find_module(args.module, [args.directory])
        assert imp.PKG_DIRECTORY in desc
        target_module = imp.load_module(args.module, f, pathname, desc)
    except ImportError:
        target_module = importlib.import_module(args.module)
    finally:
        if f is not None:
            f.close()

    return target_module


class Unpacker(object):

    def __init__(self, DIRS, args):
        self.args = args
        self.skip_existing = (not args.force_overwrite)
        self.DIRS = DIRS
        self.env, self.templates, self.values = prepare_templates(args)

    def render_and_write(self, basedir, fname, values, rename_fn=None):
        template = self.env.get_template(fname)
        dirname = os.path.dirname(fname)
        basename = os.path.splitext(os.path.basename(fname))[0]
        if rename_fn is not None:
            dirname, basename = rename_fn(dirname, basename, values)
        fn = '{}.py'.format(basename)
        full_path = os.path.join(basedir, dirname)
        if len(full_path) > 0:
            silent_mkdirs(os.path.join(full_path))
        filename = os.path.join(full_path, fn)
        if os.path.exists(filename) and self.skip_existing:
            print "{} exists: Skipped!".format(filename)
        else:
            with open(filename, 'w') as fh:
                fh.write(template.render(values))

    def _rename_test(self, dirname, fn, values):
        if fn.startswith('_') and not fn.startswith('__'):
            fn = 'test_{}{}'.format(values['name'], fn)
        return '', fn

    def _unpack(self, file_selector, directory, rename_fn=None):

        if isinstance(file_selector, basestring):
            file_selector = (lambda f: f == file_selector)

        files = [f for f in self.templates if file_selector(f)]
        for f in files:
            self.render_and_write(directory, f, self.values, rename_fn)
            self.templates.remove(f)

    def _create_init_py(self, directory):
        full_path = os.path.join(directory, '__init__.py')
        if not os.path.exists(full_path):
            with open(full_path, 'w') as fh:
                fh.write("")

    def run(self):
        # STEP 0: unpack conftest.py, plugin
        self._unpack('conftest.jinja', self.DIRS.testbase)
        self._unpack(
            'plugin.jinja', self.DIRS.twistedplugin,
            lambda _, __, values: ('', values['name']))

        self._create_init_py(self.DIRS.testbase)

        # STEP 1: test files
        self._unpack(
            lambda f: f.endswith('.jinja') and f.startswith('tests'),
            self.DIRS.test, self._rename_test)

        # STEP 2: module files
        self._unpack(
            lambda f: f.endswith('.jinja'), self.DIRS.module)


def main():
    parser = get_parser()
    args = parser.parse_args()

    target_module = get_target_module(args)

    DIRS = Dirs(args, target_module)

    up = Unpacker(DIRS, args)
    up.run()


# vim:set ft=python sw=4 et spell spelllang=en:
