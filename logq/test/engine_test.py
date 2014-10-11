# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import engine
from .. import expr as e
import tempfile

def test_cEngine():
    ef.EngineFactory.engineclass = engine.Engine
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q, list(range(len(col))))
    assert isinstance(eng, engine.Engine)
    assert eng
    assert eng.fail == 2
    for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
        s = True;
        while s:
            print("f")
            s = eng.transition(colid, c)
            print("hoge")

        if eng.is_success: break

    print("a")
    assert eng.is_success

    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q, list(range(len(col))))
    assert eng
    for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
        eng.transition(colid, c)
        if eng.is_success: break

    assert eng.is_success

    eng.reset()
    for colid, c in enumerate(['aa', 'hoge', 'hogera', 'bbb', 'poyo', 'piyo']):
        eng.transition(colid, c)
        if eng.is_success: break

    assert eng.is_success

    eng.reset()
    for colid, c in enumerate(['aa', 'hoge', 'hogera', 'bbb', 'poyo', 'uuu']):
        eng.transition(colid, c)
        if eng.is_success: break
        if eng.is_fail: break

    assert eng.is_fail
    print("hoge")

    ef.EngineFactory.engineclass = ef.PyEngine

def test_csv():
    tmp = tempfile.NamedTemporaryFile()
    tmp.write("1,2,3,4,5,6\n"\
              "a,b,hogera,1,2,piyo\n"\
              "1,2,3,4,5,6\n"\
              "1,2,\"3,4\",5,6\n"\
              "1,hoge,fuga,4,poyo,6\n"\
              "a,b,hogera,1,2,piyo\n"\
    )
    tmp.write('a,fasfafafab,hogera,"1\nabc","b""abc",piyo\n')
    fileobj = tmp.file
    fileobj.seek(0)
    ef.EngineFactory.engineclass = engine.Engine
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q, list(range(len(col))))
    parser = engine.CSVParser(eng, fileobj)
    assert parser
    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]
    print(res[3][4])
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == res[3]
