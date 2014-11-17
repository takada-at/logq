# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from ...queryparser import lexer
from ...queryparser import parser
lexer.DEBUG = 1
parser.DEBUG = 1
def test_parser():
    s = "$0 = 'hoge'"
    l = parser.parser.parse(s, lexer=lexer.lexer)
    assert l

    s = "$0 = 'hoge' OR $1 >= 'fuga'"
    l = parser.parser.parse(s, lexer=lexer.lexer)
    print(l)
    assert l

def test_parser2():
    s = '$1>="time:2014-10-01 04:04:00" and $1<"time:2014-10-01 04:05:00" and $25="user_id:3097456"'
    l = parser.parser.parse(s)
    print(l)
    assert l
