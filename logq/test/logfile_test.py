# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from ..logfile import CSVFile
from ..logfile import LTSVFile
from .. import expr as e
import logq
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

def testCSVFile2():
    import os
    fio = open(os.path.join(os.path.dirname(__file__), 'sample0.csv'))
    col = [e.Column(i) for i in range(10)]
    q = col[0] >= ''
    logfile = CSVFile(fio)
    r = list(logfile.search(q))
    for row in r:
        assert 3==len(row)
    assert 9==len(list(r))

def testLTSVFile():
    import os
    fio = open(os.path.join(os.path.dirname(__file__), 'sample0.ltsv'))
    q = logq.col('host') >= ''
    logfile = LTSVFile(fio)
    r = list(logfile.search(q))
    keys = {'host', 'ident', 'user', 'time', 'req', 'status', 'size', 'referer', 'ua'}
    for row in r:
        assert len(keys)==len(row)
        assert keys == set(dict(row).keys())

    assert 3==len(list(r))

