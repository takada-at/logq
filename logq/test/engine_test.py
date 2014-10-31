# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import engine
from .. import expr as e

def test_cEngine():
    ef.EngineFactory.engineclass = engine.Engine
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    assert isinstance(eng, engine.Engine)
    assert eng
    assert eng.fail == 2
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
    for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
        if colid in colids:
            eng.transition(colids[colid], c)

        if eng.is_success: break

    print("a")
    assert eng.is_success

    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
    eng = ef.compile_query(q)
    assert eng
    for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
        if colid in colids:
            eng.transition(colids[colid], c)
        if eng.is_success: break

    assert eng.is_success

    eng.reset()
    for colid, c in enumerate(['aa', 'hoge', 'hogera', 'bbb', 'poyo', 'piyo']):
        if colid in colids:
            eng.transition(colids[colid], c)
        if eng.is_success: break

    assert eng.is_success

    eng.reset()
    for colid, c in enumerate(['aa', 'hoge', 'hogera', 'bbb', 'poyo', 'uuu']):
        if colid in colids:
            eng.transition(colids[colid], c)
        if eng.is_success: break
        if eng.is_fail: break

    assert eng.is_fail
    print("hoge")

    ef.EngineFactory.engineclass = ef.PyEngine

