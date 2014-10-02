# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from collections import Counter, defaultdict
from itertools import combinations
from .logic import Atomic, Bool, And, Or, Not

class StateFactory(object):
    def __init__(self):
        self.states = Counter()
    def new_state(self, context='_default'):
        c = self.states[context]
        self.states[context] += 1
        return c

class FA(object):
    def __init__(self):
        self.map_ = {}
        self.start = None
        self.accepts = set()
    def __repr__(self):
        return str(self._states)
    def __or__(self, other):
        new = self.__class__()
        new.map_ = deepcopy(self.map_)
        return new
    def is_accept_state(self, state):
        return state in self.accepts
    def get_links(self, state, input_=None, exclusive=''):
        links = []
        for (s0, i), s1 in self.map_.items():
            if s0!=state: continue
            if isinstance(s1, set):
                for ns in s1: links.append((i, ns))
            else:
                links.append((i, s1))

        if input_ is not None:
            links = {link for link in links if link[0]==input_}
        if exclusive is not None:
            links = {link for link in links if link[0]!=exclusive}
        return links
    def link(self, state, input_, nextstate):
        self._add_map(state, input_, nextstate)

class NFA(FA):
    def _add_map(self, state, input_, nextstate):
        args = (state, input_)
        self.map_.setdefault(args, set())
        self.map_[args].add(nextstate)

class DFA(FA):
    def to_table(self):
        states = set()
        inputs = set()
        for (state0, input_), state1 in self.map_.items():
            states.add(state0); states.add(state1)
            inputs.add(input_)

        states = list(states)
        inputs = list(inputs)
        states.sort()
        inputs.sort()
        table = [[''] + inputs]
        table += [[state] + [self.map_.get((state, i)) for i in inputs] for state in states]
        return table

    def _add_map(self, state, input_, nextstate):
        args = (state, input_)
        self.map_[args] = nextstate

class Converter():
    dfaclass = DFA
    def dfa(self, nfa, factory):
        newstart, newmap = self._convertlink(nfa)
        return self._create_dfa(factory, newmap, nfa, newstart)
    def extends(self, nfa, states):
        res = set(states)
        for state in states:
            links = nfa.get_links(state, input_='', exclusive=None)
            res.update({link[1] for link in links})

        return frozenset(res)
    def _convertlink(self, nfa):
        newstart = self.extends(nfa, {nfa.start})
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
                extended = self.extends(nfa, states)
                newlink = (curstates, input_)
                newmap[newlink] =  extended
                if extended not in statecache:
                    stack.append(extended)

        return newstart, newmap
    def _create_dfa(self, factory, map_, nfa, newstart):
        def createnumstate(statecache, factory, state):
            if state not in statecache:
                numstate = factory.new_state()
                statecache[state] = numstate

            return statecache[state]
        def isfinal(state, nfa):
            return any(nfa.is_accept_state(stat) for stat in state)

        dfa = self.dfaclass()
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

class Engine(object):
    def __init__(self):
        self.table = []

class Expr(Atomic):
    def __and__(self, other):
        return qAnd(self, other)
    def __or__(self, other):
        return qOr(self, other)
    def __invert__(self):
        return qNot(self)

class StringEq(Expr):
    def __init__(self, colname, queryword):
        self.colname = colname
        self.queryword = queryword
        self.ops = ('=', queryword)
    def construct(self):
        eng = Engine()
        row = dict()
        row[self.colname] = [self.ops]
        eng.table.append(row)
        return eng

class qAnd(And):
    def construct(self, factory):
        children = self.children()
        children.sort(key=lambda x: list(x.variables)[0].colname)
        eng = Engine()
        row = dict()
        for child in children:
            e0 = child.construct()
            for k, v in e0:
                row.setdefault(k, [])
                row[k] += v

        eng.table.append(row)
        return eng

class qOr(Or):
    def construct(self, factory):
        automaton = NFAEngine()
        start = factory.new_state()
        automaton.start = start
        children = self.children()
        nfas = [c.construct(factory) for c in children]
        for i, nfa0 in enumerate(nfas):
            automaton.link(start, '', nfa0.start)
            others = nfas[:i] + nfas[i+1:]
            for nfa1 in others:
                for (s, input_), ns in nfa1.map.items():
                    automaton.link(start, '', s)

        return automaton

class qNot(Not):
    @property
    def colname(self):
        return self.child.colname
    def invert(self, op):
        if op=='=':
            return '!='
    def construct(self, factory):
        child = self.child
        nfa = child.construct(factory)
        nfa2 = NFAEngine()
        nfa2.start = nfa.start
        nfa2 |= nfa
        newmap = {}
        for (s, input_), v in nfa.map_.items():
            input2 = (self.invert(input_[0]), input_[1])
            newmap[s, input_2] = v

        nfa2.map_ = newmap

        automaton = NFAEngine()
        start = factory.new_state()
        automaton |= nfa2
        automaton.link(start, '', nfa2.start)
        automaton.accepts = nfa2.accepts
        return automaton
