# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import enginefactory as ef
from .. import col
from .. import engine
import tempfile
def test_csv_read():
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
    q = (col(1)=="hoge") & (col(2)=="fuga") & (col(4)=="poyo") | (col(2)=="hogera") & (col(5)=="piyo")
    eng = ef.compile_query(q)
    colmap = q.col_list()
    print(colmap)
    parser = engine.CSVParser(eng, fileobj, colmap)
    result = []
    for i in range(20):
        res = parser.read(10)
        result += res

    assert result
    assert 4==len(result)
    assert [['a', 'b', 'hogera', '1', '2', 'piyo'], ['1', 'hoge', 'fuga', '4', 'poyo', '6'], ['a', 'b', 'hogera', '1', '2', 'piyo']] == result[:3]
    assert ['a','fasfafafab','hogera',"1\nabc","b\"abc",'piyo'] == result[3]


    fileobj.seek(0)
    res = parser.read()
    assert 4==len(res)


