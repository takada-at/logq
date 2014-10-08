# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import engine
from .. import expr as e

def test_cEngine():
    ef.EngineFactory.engineclass = engine.Engine
    fac = ef.EngineFactory()
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = q.compile(list(range(len(col))))
    assert isinstance(eng, engine.Engine)
    assert eng
    # for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
    #     s = True;
    #     while s:
    #         s = eng.transition(colid, c)

    #     if eng.is_success: break

    # assert eng.is_success
