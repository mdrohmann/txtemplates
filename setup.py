import ez_setup
ez_setup.use_setuptools()

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='txtemplates',
    description='Templates to quickly create twisted servers',
    author='Martin C Drohmann',
    author_email='mcd@askthevotegoat.com',
    version='0.3.1',
    install_requires=['twisted', 'pytest', 'pytest-twisted'],
    scripts=['scripts/make_new_server.py'],
    package_data={
        'txtemplates.server_templates': [
            'templates/*.jinja', 'templates/*/*.jinja'],
    },
    license='LICENSE',
    packages=find_packages(),
    cmdclass={'test': PyTest},
    )
