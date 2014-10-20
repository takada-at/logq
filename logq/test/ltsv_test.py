# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import enginefactory as ef
from .. import engine
from .. import expr as e
import tempfile

def test_ltsv():
    tmp = tempfile.NamedTemporaryFile()
    tmp.write("one:1\ttwo:2\tthree:3\n"\
              "one:a\ttwo:b\tthree:hogera\n"\
              "one:1\ttwo:2\tthree:hoge\n"\
    )
    fileobj = tmp.file
    fileobj.seek(0)
    ef.EngineFactory.engineclass = engine.Engine
    col = e.Column
    cols = [col('one'), col('two'), col('three')]
    q = (cols[0]=="hoge") & (cols[1]=="fuga") | (cols[2]=="hogera")
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    print(colmap)
    parser = engine.LTSVParser(eng, fileobj, colmap)
    assert parser
    res = list(parser)
    assert 1==len(res)


    q = col('three').contains('hoge')
    eng = ef.compile_query(q)
    colmap = {str(k): v for k, v in q.columns()}
    fileobj.seek(0)
    parser = engine.LTSVParser(eng, fileobj, colmap)
    res = list(parser)
    assert 2==len(res)

