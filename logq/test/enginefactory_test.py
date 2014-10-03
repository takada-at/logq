# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import expr as e

def test_EngineFactory():
    fac = ef.EngineFactory()
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    q.normalize()
    opcodes = q._construct()
    cols = [c.colname for c in col]
    eng=fac.construct(opcodes, cols=cols)
    assert eng
    print('')
    print(eng.format())
