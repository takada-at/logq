# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .. import engine

def test_NFA():
    u"""
    test for engine.convert_nfa2dfa
    """
    fac = engine.StateFactory()
    nfa = engine.NFA()
    states = [fac.new_state() for i in range(10)]
    start = states[0]
    # sample
    # 0 -->  1 -a-> 2 -b-> 3 -b-> 4 -d-> 5
    #   -->  6 -a-> 7 -c-> 8 -c-> 9
    # dfa:
    # 0 -a-> 1 -b-> 2 -b-> 3 -d-> 4
    #          -c-> 5 -c-> 6
    nfa.start = states[0]
    nfa.link(start, '', states[1])
    nfa.link(states[1], 'a', states[2])
    nfa.link(states[2], 'b', states[3])
    nfa.link(states[3], 'b', states[4])
    nfa.link(states[4], 'd', states[5])
    nfa.accepts.add(states[5])

    nfa.link(start, '', states[6])
    nfa.link(states[6], 'a', states[7])
    nfa.link(states[7], 'c', states[8])
    nfa.link(states[8], 'c', states[9])
    nfa.accepts.add(states[9])

    assert {('', 1), ('',6)} == nfa.get_links(nfa.start, '', exclusive=None)
    fac = engine.StateFactory()
    cvt = engine.Converter()
    dfa = cvt.dfa(nfa, fac)
    assert dfa
    table = dfa.to_table()
    print(table)
    assert 8==len(table)
    assert ['', 'a', 'b', 'c', 'd'] == table[0]
