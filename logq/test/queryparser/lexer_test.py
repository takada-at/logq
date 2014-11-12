# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from ...queryparser import lexer
from ...queryparser import parser
lexer.DEBUG = 1
parser.DEBUG = 1

def test_lexer():
    s = "$0 = 'hoge'"
    lexer.lexer.input(s)
    L = []
    while True:
        tok = lexer.lexer.token()
        if tok: L.append(tok)
        else: break

    assert 3 == len(L)
    col = L[0].value
    assert '0' == col.colname
