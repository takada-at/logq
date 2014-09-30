# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import operator

class Bool(object):
    @classmethod
    def create(cls, ite):
        u"""
        >>> a, b, c = Bool.create('abc')
        >>> a | b
        a | b
        """
        return [Atomic(c) for c in ite]

    def __init__(self, *args):
        self.args = args

    @property
    def atomic(self):
        return isinstance(self, Atomic)

    @property
    def variables(self):
        if self.atomic:
            return set([self])
        else:
            return reduce(lambda x,y: x | y.variables, self.args, set())

    def normalize(self):
        return self
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return self.name == other
    def __ne__(self, other):
        return self.name != other
    def __and__(self, other):
        return And(self, other)
    def __or__(self, other):
        return Or(self, other)
    def __invert__(self):
        return Not(self)
    def __contains__(self, other):
        return self==other
    def __hash__(self):
        return ~hash(self.name)
    def format(self, term):
        if term.atomic or isinstance(term, UnaryTerm):
            return str(term)
        elif isinstance(self, Or) and isinstance(term, And):
            return str(term)
        else:
            return "({})".format(term)

class Atomic(Bool):
    def __init__(self, *args):
        self.name = args[0]
        self.args = []

class UnaryTerm(Bool):
    op = ''
    def __init__(self, *args):
        self.args = args
        self.child = args[0]
        child = self.format(self.child)
        self.name = '{}{}'.format(self.op, child)
        self._mark = False
    def __contains__(self, other):
        return other in self.args

class BinaryTerm(Bool):
    op = ''
    def __init__(self, *args):
        self.args = args
        self.fst = args[0]
        self.snd = args[1]
        fst = self.format(self.fst)
        snd = self.format(self.snd)
        self.name = '{} {} {}'.format(fst, self.op, snd)
        self._mark = False
    def children(self):
        """
        >>> a, b, c, d = Bool.create('abcd')
        >>> ((b & c) & d).children()
        [b, c, d]
        """
        klass = self.__class__
        if not isinstance(self.fst, klass) and not isinstance(self.snd, klass):
            return [self.fst, self.snd]
        if isinstance(self.fst, klass):
            children = self.fst.children()
        else:
            children = [self.fst]

        if isinstance(self.snd, klass):
            children += self.snd.children()
        else:
            children += [self.snd]

        return children
    def __contains__(self, other):
        return other in self.args
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            this = self
            return (this.fst == other.fst and this.snd == other.snd) or (this.fst == other.snd and this.snd == other.fst)
        else:
            return False
    def __ne__(self, other):
        return not(self==other)
    def filter_children(self, children):
        marks = set()
        if isinstance(self, And): dual = Or
        elif isinstance(self, Or): dual = And
        for idx0 in range(len(children)-1):
            x = children[idx0]
            for idx1 in range(idx0+1, len(children)):
                y = children[idx1]
                # A & A -> A
                # A | A -> A
                if x == y: marks.add(idx1)
                # (A|B) & A -> A
                elif isinstance(x, dual) and y in x: marks.add(idx0)
                # A & (A|B) -> A
                # A | (A&B) -> A
                elif isinstance(y, dual) and x in y: marks.add(idx1)

        return [c for idx, c in enumerate(children) if idx not in marks]

class And(BinaryTerm):
    op = '&'
    def normalize(self):
        """
        example ::

        >>> a, b, c, d = Bool.create('abcd')
        >>> (a & a).normalize()
        a
        >>> ((a|b) & a).normalize()
        a
        >>> ((a|b) & b) & c).normalize()
        a & b & c | b & c
        """
        if self._mark: return self
        children = self.children()
        leng = len(children)
        children = self.filter_children(children)
        if leng!=len(children):
            return reduce(operator.and_, children).normalize()

        if isinstance(self.fst, Or):
            # (A | B) & C -> A & C | B & C
            return (self.fst.fst & self.snd | self.fst.snd & self.snd).normalize()
        elif isinstance(self.snd, Or):
            # A & (B | C) -> A & B | A & C
            return (self.fst & self.snd.fst | self.fst & self.snd.snd).normalize()

        flag = False
        L = []
        for c in children:
            c2 = c.normalize()
            if c!=c2: flag = True
            L.append(c2)

        children = L
        # if one element normalized, reconstruct all
        if flag:
            return reduce(operator.and_, children).normalize()

        self._mark = True
        return self

class Or(BinaryTerm):
    op = '|'
    def normalize(self):
        if self._mark: return self
        children = self.children()
        leng = len(children)
        children = self.filter_children(children)
        if leng!=len(children):
            return reduce(operator.or_, children).normalize()

        flag = False
        L = []
        for c in children:
            c2 = c.normalize()
            if c!=c2: flag = True
            L.append(c2)

        children = L
        # if one element normalized, reconstruct all
        if flag:
            return reduce(operator.or_, children).normalize()

        self._mark = True
        return self

class Not(UnaryTerm):
    op = '~'
    def normalize(self):
        if self._mark: return self
        arg = self.child
        # ~(a & b) -> ~a | ~b
        if isinstance(arg, And):
            left  = ~arg.fst
            right = ~arg.snd
            return (left.normalize() | right.normalize()).normalize()
        # ~(a | b) -> ~a & ~b
        elif isinstance(arg, Or):
            left  = ~arg.fst
            right = ~arg.snd
            return (left.normalize() & right.normalize()).normalize()
        # ~~a -> a
        elif isinstance(arg, Not):
            return arg.child.normalize()

        tmp = arg.normalize()
        if tmp!=arg:
            return ~tmp

        self._mark = True
        return self

class LogicalTree(object):
    def __init__(self, ids, expr):
        assert isinstance(ids, set)
        self.ids   = ids
        self.expr  = expr
        self._merged = False
        self.mark  = None
    def compair(self, other):
        diff = _compair(self.expr, other.expr)
        if len(diff)==1:
            return self.merge(diff, other)
        else:
            return None
    def merge(self, diff, other):
        merged = self.expr[:]
        expr = merged[diff[0]] = '_'
        ids  = self.ids | other.ids
        return self.__class__(ids, expr)

def quine_mccluskey(term):
    term = term.normalize()
    disjuncts = term.children()
    variables = list(term.variables)
    variables.sort(lambda x,y: cmp(x.name, y.name))
    minterns = step0_minterms(variables, term)
    # convert to list of 1/0
    bins = tobin(variables, minterns)
    prime_implicants = step1_prime_implicants(bins)

def step0_minterms(variables, term):
    newdisjuncts = []
    disjuncts = term.children()
    for disjunct in disjuncts:
        L = [disjunct.children()]
        for var in variables:
            L2 = []
            for term in L:
                # A & B -> A & B & C | A & B & ~C
                if var not in term and ~var not in term:
                    L2.append(term + [var])
                    L2.append(term + [~var])
                else:
                    L2.append(term)

            L = L2

        newdisjuncts += L

    return _normalize_terms(variables, newdisjuncts)

def _normalize_terms(variables, terms):
    res = []
    cache = set()
    for disjunct in terms:
        terms  = []
        for var in variables:
            if ~var in disjunct:
                terms.append(~var)
            elif var in disjunct:
                terms.append(var)

        tm = reduce(operator.and_, terms)
        # delete not unique terms
        if tm.name in cache:
            continue

        cache.add(tm.name)
        res.append(tm)

    return res

def tobin(variables, term):
    res = []
    for var in variables:
        children = term.children()
        if ~var in children:
            res.append(0)
        elif var in children:
            res.append(1)

    return res

def step1_prime_implicants(terms):
    trees = [LogicalTree({idx}, term) for idx, term in enumerate(terms)]
    merged, _ = _merge(trees)
    primes = []
    while merged:
        merged, marked = _merge(merged, enable_mark=True)
        primes += marked

    return primes

def _merge(terms, enable_mark=False):
    pairs = []
    for term0 in terms:
        for term1 in terms[i+1:]:
            merged = term0.compair(term1)
            if merged:
                if enable_mark:
                    term0._merged = True
                    term1._merged = True

                pairs.append(merged)

    if enable_mark:
        marked = [term for term in terms if not term._merged]
    else:
        marked = None

    return (pairs, marked)

def _compair(x,y):
    res = []
    for i in range(len(x)):
        if x[i]!=y[i]:
            res.append(res)

    return res

def step2_essential_prime_implicants(implicants):
    pass
