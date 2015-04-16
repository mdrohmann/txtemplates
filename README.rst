#################
Twisted templates
#################

This is a compilation of python scripts and modules to quickly develop and test
python server modules.


Quick usage
===========

Create a source directory `SOURCE_DIR` with a main source package refered to as
`PACKAGE` in it, that can be empty ie., only contain an `` __init__.py`` file.
Running

.. code:: bash

   make_new_server.py -C SOURCE_DIR NAME PACKAGE

creates a module `PACKAGE.NAME` with template files to quickly develop a
server.  Start by running the tests, added to the directory
`` SOURCE_DIR/tests/NAME/`` with py.test:

.. code:: bash

   py.test --twisted tests/NAME/

You can add functionality similar to the demonstration server
``txtemplates.echo``.
