# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

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
        self._links = {}
        self._states = set()
        self._inputs = set()
    def __repr__(self):
        return str(self._states)
    def is_accept_state(self, state):
        return state in self.accepts
    def get_links(self, state, input_=None, exclusive=''):
        links = self._links.get(state, set())
        if input_ is not None:
            links = {link for link in links if link[0]==input_}
        if exclusive is not None:
            links = {link for link in links if link[0]!=exclusive}
        return links
    def link(self, state, input_, nextstate):
        self._inputs.add(input_)
        self._states.add(state)
        self._states.add(nextstate)
        link = (input_, nextstate)
        self._links.setdefault(state, set())
        self._links[state].add(link)
        self._add_map(state, input_, nextstate)

class NFA(FA):
    def _add_map(self, state, input_, nextstate):
        args = (state, input_)
        self.map_.setdefault(args, set())
        self.map_[args].add(nextstate)

class DFA(FA):
    def to_table(self):
        states = list(self._states)
        inputs = list(self._inputs)
        states.sort()
        inputs.sort()
        table = [[''] + inputs]
        table += [[state] + [self.map_.get((state, i)) for i in inputs] for state in states]
        return table

    def _add_map(self, state, input_, nextstate):
        args = (state, input_)
        self.map_[args] = nextstate

def convert_nfa2dfa(nfa, factory):
    newstart, newmap = _convertlink(nfa)
    return _create_dfa(factory, newmap, nfa, newstart)

def _convertlink(nfa):
    def extends(nfa, states):
        res = set(states)
        for state in states:
            links = nfa.get_links(state, input_='', exclusive=None)
            res.update({link[1] for link in links})

        return frozenset(res)

    newstart = extends(nfa, set([nfa.start]))
    stack = [newstart]
    statecache = set()
    newmap = dict()
    while stack:
        curstates = stack.pop()
        newstates = dict()
        for nfastate in curstates:
            links = nfa.get_links(nfastate, input_=None, exclusive='')
            for input_, state in links:
                newstates.setdefault(input_, set())
                newstates[input_].add(state)

        statecache.add(frozenset(curstates))
        for input_, states in newstates.items():
            extended = extends(nfa, states)
            newlink = (curstates, input_)
            newmap[newlink] =  extended
            if extended not in statecache:
                stack.append(extended)
    return newstart, newmap

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
    for (state0, input_), state1 in map_.items():
        numstate0 = createnumstate(statecache, factory, state0)
        if isfinal(state0, nfa):
            dfa.accepts.add(numstate0)

        numstate1 = createnumstate(statecache, factory, state1)
        dfa.link(numstate0, input_, numstate1)
        if isfinal(state1, nfa):
            dfa.accepts.add(numstate1)

    return dfa


