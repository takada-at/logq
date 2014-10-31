# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import expr as e

def test_EngineFactory():
    reload(ef)
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
    assert eng
    print(q)
    print(eng.format())
    state = 0
    col = colids[1]
    op = eng.exprs
    # 最初は =hoge
    a = eng.expr_table[state][col]
    assert ('=', 'hoge') == op[ a ]

    # 成功したら次は =fuga or =hogera
    state = eng.success_table[state][col]
    col = colids[2]
    a = eng.expr_table[state][col]
    assert ('=', 'fuga') == op[ a ] or ('=', 'hogera') == op[ a ]

    if op[a] == ('=', 'fuga'):
        state0 = eng.success_table[state][col]
        state1 = eng.fail_table[state][col]
        assert ('=', 'hogera') == op[ eng.expr_table[state0][col] ]
        assert ('=', 'hogera') == op[ eng.expr_table[state1][col] ]
    elif op[a] == ('=', 'hogera'):
        state0 = eng.success_table[state][col]
        state1 = eng.fail_table[state][col]
        assert ('=', 'fuga') == op[ eng.expr_table[state0][col] ]
        assert ('=', 'fuga') == op[ eng.expr_table[state1][col] ]

    # =fugaに成功したら =hogeraの次は=poyo
    # さらに成功したら終了
    state = eng.success_table[state0][col]
    col = colids[4]
    assert ('=', 'poyo') == op[ eng.expr_table[state][col] ]
    assert eng.success == eng.success_table[state][col]

def test_Engine():
    reload(ef)
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    assert eng
    print(q)
    print(eng.format())
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
    for colid, c in enumerate(['aa', 'hoge', 'fuga', 'bbb', 'poyo', 'fa']):
        if colid in colids:
            print(colids[colid], c)
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

def test_EngineFactory2():
    reload(ef)
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    col = [e.Column(i) for i in range(10)]
    q = (col[0]=="a")
    eng = ef.compile_query(q)
    assert eng
    print(eng.format())

def test_EngineFactory3():
    reload(ef)
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    col = [e.Column(i) for i in range(10)]
    q = (col[2] >= "hoge") & (col[0]=='a') & (col[2]<='hoge')
    eng = ef.compile_query(q)
    assert eng
    print(eng.format())
    assert eng.success_table[0][0]!=1

def test_EngineFactory4():
    cols = [e.Column(i) for i in range(10)]
    q = (cols[1]=='hoge') | (cols[2]=='fuga') & (cols[4]=='poyo') | (cols[2]=='hogera') & (cols[5]=='piyo')
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    eng = ef.compile_query(q)
    assert eng
    print(q)
    print(eng.format())

def test_EngineFactory5():
    cols = [e.Column(i) for i in range(10)]
    q = (cols[0] >= '2014-10-03 12:00:00') & (cols[0] < '2014-10-03 12:02:00') & (cols[1]=='hoge')
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    eng = ef.compile_query(q)
    print(q)
    print(eng.format())
    data = [
        ["2014-10-03 12:00:11", "hoge"],
        ["2014-10-03 12:01:11", "hoge"],
        ["2014-10-03 12:01:11", "fuga"],
        ["2014-10-03 12:10:11", "hoge"],
        ]
    cnt = 0
    for row in data:
        eng.reset()
        for colid, val in enumerate(row):
            eng.transition(colid, val)

        if eng.is_success:
            cnt += 1

    assert 2 == cnt

