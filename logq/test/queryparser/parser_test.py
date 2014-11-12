# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from ...queryparser import lexer
from ...queryparser import parser
lexer.DEBUG = 1
parser.DEBUG = 1
def test_parser():
    s = "$0 = 'hoge'"
    l = parser.parser.parse(s)
    assert l

    s = "$0 = 'hoge' OR $1 >= 'fuga'"
    l = parser.parser.parse(s)
    print(l)
    assert l
