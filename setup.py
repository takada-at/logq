# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from distutils.core import setup, Extension

setup(name='logq',
      version='0.0.1',
      description='',
      author='takada-at',
      author_email='takada-at@klab.com',
      packages=['logq', 'logq.test'],
      ext_modules=[
        Extension('logq.engine', ['logq/src/cenginemodule.c'])
        ],
     )
