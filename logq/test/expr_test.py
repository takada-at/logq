# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import expr as e

def test_Engine():
    col = [e.Column(i) for i in range(10)]
    s = col[1]=="hoge"
    assert isinstance(s, e.StringEq)
    assert isinstance(s|s, e.qOr)
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    q.normalize()
    opcodes = q._construct()
    row = opcodes.table[0]
    assert row[1] == [("=", "hoge")]
    assert row[2] == [("=", "fuga")]
    assert row[4] == [("=", "poyo")]

    row = opcodes.table[1]
    assert row[2] == [("=", "hogera")]
    assert row[5] == [("=", "piyo")]


