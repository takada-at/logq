# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import expr as e

def test_EngineFactory():
    reload(ef)
    fac = ef.EngineFactory()
    ef.EngineFactory.set_engineclass(ef.PyEngine)
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    eng = ef.compile_query(q)
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
    assert eng
    print('')
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
    print(col)
    a = eng.expr_table[state][col]
    assert ('=', 'fuga') == op[ a ] or ('=', 'hogera') == op[ a ]

    # 成功しても失敗しても次は = hogera
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
    colids = {colname: cid for cid, colname in enumerate((1,2,4,5))}
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

