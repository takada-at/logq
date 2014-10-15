# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import enginefactory as ef
from .. import engine
from .. import expr as e
import tempfile

def test_csv():
    return
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
    eng = ef.compile_query(q)
    parser = engine.CSVParser(eng, fileobj)
    assert parser
    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]
    print(res[3][4])
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == res[3]

def test_csv2():
    return
    tmp = tempfile.NamedTemporaryFile()
    tmp.write("1,2,3,4,5,6\n"\
              "a,b,hogera,1,2,piyo\n"\
              "1,2,3,4,5,6\n"\
              "1,2,\"3,4\",5,6\n"\
              "1,hoge,fuga,4,poyo,6\n"\
              "a,b,hogera,1,2,piyo\n"\
    )
    tmp.write('a,fasfafafab,hogera,"1\nabc","b""abc",piyo\n')
    tmp.seek(0)
    ef.EngineFactory.engineclass = engine.Engine
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    parser = engine.CSVParser(eng, tmp)
    assert parser
    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]
    print(res[3][4])
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == res[3]
