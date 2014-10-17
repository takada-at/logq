# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import enginefactory as ef
from .. import engine
from .. import expr as e
import tempfile

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
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    print(colmap)
    parser = engine.CSVParser(eng, fileobj, colmap)
    assert parser
    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]
    print(res[3][4])
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == res[3]

def test_csv2():
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
    colmap = {str(k): v for k, v in q.columns()}
    parser = engine.CSVParser(eng, tmp, colmap)
    assert parser
    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]
    print(res[3][4])
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == res[3]

    tmp.seek(0)
    q2 = (col[1].contains('og')) & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    parser = engine.CSVParser(eng, tmp, colmap)

    res = list(parser)
    assert 4==len(res)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == res[:3]


def test_csv3():
    tmp = tempfile.NamedTemporaryFile()
    tmp.write("1\t2\t3\t4\t5\t6\n"\
              "a\tb\thogera\t1\t2\tpiyo\n"\
              "1\t2\t3\t4\t5\t6\n"\
              "1\t2\t\"3\t4\"\t5\t6\n"\
              "1\thoge\tfuga\t4\tpoyo\t6\n"\
              "a\tb\thogera\t1\t2\tpiyo\n"\
    )
    tmp.write('a\tfasfafafab\thogera\t"1\nabc"\t"b""abc"\tpiyo\n')
    fileobj = tmp.file
    fileobj.seek(0)
    ef.EngineFactory.engineclass = engine.Engine
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    print(colmap)
    parser = engine.CSVParser(eng, fileobj, colmap, delimiter=b"\t")
    assert parser
    res = list(parser)
    assert 4==len(res)

    q = col[0]=="a"
    fileobj.seek(0)
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    parser = engine.CSVParser(eng, fileobj, colmap, delimiter=b"\t")
    assert 3==len(list(parser))


    line = 'hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,hoge,fuga'
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(line)
    fileobj = tmp.file

    fileobj.seek(0)
    q = e.Column(0)=='hoge'
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    parser = engine.CSVParser(eng, fileobj, colmap)
    assert 1==len(list(parser))

    fileobj.seek(0)
    q = e.Column(50)=="fuga"
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    parser = engine.CSVParser(eng, fileobj, colmap)
    assert 1==len(list(parser))

    import io
    parser = engine.CSVParser(eng, io.BytesIO(b''), colmap)
    parser = engine.CSVParser(eng, io.BytesIO(b'\n'), colmap)
    parser = engine.CSVParser(eng, io.BytesIO(b'abc\n'), colmap)
