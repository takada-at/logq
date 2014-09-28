# coding:utf-8

class StateFactory(object):
    def __init__(self, init=0):
        self.state = init
    def new_state(self):
        res = self.state
        self.state += 1
        return res

class FA(object):
    def __init__(self):
        self.map_ = {}
        self.start = None
        self.accepts = set()
        self.links = {}
    def is_accept_state(self, state):
        return state in self.accepts
    def get_links(self, state, char=None, exclusive=''):
        links = self.links.get(state, set())
        if char is not None:
            links = {link for link in links if link[1]==char}
        if exclusive is not None:
            links = {link for link in links if link[1]!=exclusive}
        return links
    def link(self, state, char, nextstate):
        link = (state, char)
        self.links.setdefault(state, set())
        self.links[state].add(link)
        self._add_map(link, nextstate)

class NFA(FA):
    def _add_map(self, link, nextstate):
        self.map_.setdefault(link, set())
        self.map_[link].add(nextstate)

class DFA(FA): 
    def _add_map(self, link, nextstate):
        self.map_[link] = nextstate

def convert_nfa2dfa(nfa, factory):
    def extends(nfa, states):
        res = set(states)
        for state in states:
            res.update(nfa.get_links(state, char='', exclusive=None))

        return frozenset(res)

    newstart = extends(nfa, set([nfa.start]))
    stack = [newstart]
    statecache = set()
    newmap = dict()
    while stack:
        curstates = stack.pop()
        newstates = dict()
        for nfastate in curstates:
            links = nfa.get_links(nfastate, char=None, exclusive='')
            for state, char in links:
                newstates.setdefault(char, set(curstates))
                newstates[char].remove(nfastate)
                newstates[char].add(state)

        statecache.add(frozenset(curstates))
        for char, states in newstates.items():
            extended = extends(nfa, states)
            newlink = (curstates, char)
            newmap[newlink] =  extended
            if extended not in statecache:
                stack.append(extended)

    return _create_dfa(factory, newmap, nfa, newstart)

def _create_dfa(factory, map_, nfa, newstart):
    def createnumstate(statecache, factory, state):
        if state not in statecache:
            numstate = factory.new_state()
            statecache[state] = numstate

        return statecache[state]

    def isfinal(state, nfa):
        return any(nfa.is_accept_state(stat) for stat in state)

    dfa = DFA()
    statecache = dict()
    newmap = dict()
    dfa.start = createnumstate(statecache, factory, newstart)
    for (state0, char), state1 in map_.items():
        numstate0 = createnumstate(statecache, factory, state0)
        if isfinal(state0):
            dfa.accepts.add(numstate0)

        numstate1 = createnumstate(statecache, factory, state1)
        dfa.link(numstate0, char, numstate1)
        if isfinal(state1):
            dfa.accepts.add(numstate1)

    return dfa


