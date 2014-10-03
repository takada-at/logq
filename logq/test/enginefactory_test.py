# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import enginefactory as ef
from .. import expr as e

def test_EngineFactory():
    fac = ef.EngineFactory()
    col = [e.Column(i) for i in range(10)]
    q = (col[1]=="hoge") & (col[2]=="fuga") & (col[4]=="poyo") | (col[2]=="hogera") & (col[5]=="piyo")
    q.normalize()
    opcodes = q._construct()
    cols = [c.colname for c in col]
    eng=fac.construct(opcodes, cols=cols)
    assert eng
    print('')
    print(eng.format())
    state = 0
    col = 1

    op = eng.exprs
    # 最初は =hoge
    a = eng.action_table[state][col]
    assert ('=', 'hoge') == op[ a ]

    # 成功したら次は =fuga
    state = eng.success_table[state][col]
    col = 2
    a = eng.action_table[state][col]
    assert ('=', 'fuga') == op[ a ]

    # 成功しても失敗しても次は = hogera
    state0 = eng.success_table[state][col]
    state1 = eng.fail_table[state][col]
    assert ('=', 'hogera') == op[ eng.action_table[state0][col] ]
    assert ('=', 'hogera') == op[ eng.action_table[state1][col] ]

    # =fugaに成功したら =hogeraの次は=poyo
    # さらに成功したら終了
    state = eng.success_table[state0][col]
    col = 4
    assert ('=', 'poyo') == op[ eng.action_table[state][col] ]
    assert eng.success == eng.success_table[state][col]
