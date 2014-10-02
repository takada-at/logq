# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import engine as e

def test_Engine():
    col = [e.Column(i) for i in range(10)]
    s = col[1]=="hoge"
    assert isinstance(s, e.StringEq)
    assert isinstance(s|s, e.qOr)
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    engine = q.compile()
    assert engine
    print(engine.opcodes.table)
    row = engine.opcodes.table[0]
    assert row[1] == [("=", "hoge")]
    assert row[2] == [("=", "fuga")]
    assert row[4] == [("=", "poyo")]

    row = engine.opcodes.table[1]
    assert row[2] == [("=", "hogera")]
    assert row[5] == [("=", "piyo")]


