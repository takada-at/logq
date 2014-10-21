# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from ..logfile import CSVFile
from .. import expr as e
import tempfile

def testCSVFile():
    tmp = tempfile.NamedTemporaryFile()
    tmp.write("1,2,3,4,5,6\n"\
              "a,b,hogera,1,2,piyo\n"\
              "1,2,3,4,5,6\n"\
              "1,2,\"3,4\",5,6\n"\
              "1,hoge,fuga,4,poyo,6\n"\
              "a,b,hogera,1,2,piyo\n"\
    )
    tmp.seek(0)
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    logfile = CSVFile(tmp)
    r = logfile.search(q)
    assert 3==len(list(r))

    q = (col[2] >= "hoge") & (col[0]=='a')
    print(q)
    tmp.seek(0)
    logfile = CSVFile(tmp)
    r = logfile.search(q)
    assert 2==len(list(r))

def testCSVFile():
    import os
    fio = open(os.path.join(os.path.dirname(__file__), 'sample0.csv'))
    col = [e.Column(i) for i in range(10)]
    q = col[0] >= ''
    logfile = CSVFile(fio)
    r = list(logfile.search(q))
    assert 4==len(list(r))

