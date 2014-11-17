# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from setuptools import setup, find_packages, Extension

from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        import pytest
        pytest.main(self.test_args)

setup(name='logq',
      version='0.0.1',
      description='',
      author='takada-at',
      author_email='takada-at@klab.com',
      scripts=['scripts/logqsearch.py'],
      packages=find_packages(),
      ext_modules=[
          Extension('logq.engine', 
                    ['logq/src/module.c', 'logq/src/engine.c', 'logq/src/colmap.c', 
                     'logq/src/csv.c', 'logq/src/ltsv.c'])

      ],
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
)

