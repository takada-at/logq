from .. import engine

def test_convert_nfa2dfa():
    fac = engine.StateFactory()
    nfa = engine.NFA()
    states = [fac.new_state() for i in range(10)]
    start = states[0]
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

    dfa = engine.convert_nfa2dfa(nfa, fac)
    assert dfa

