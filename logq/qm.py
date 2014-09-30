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

def disjunctlist(form):
    u"""
    >>> a, b, c, d = Bool.create('abcd')
    >>> disjunctlist(((a | b) | c) | d)
    [a, b, c, d]
    """
    # ((a | b) | c) | d
    ptr = form
    disjuncts = []
    while ptr:
        if isinstance(ptr, Or):
            disjuncts.append(ptr.snd)
            ptr = ptr.fst
        else:
            disjuncts.append(ptr)
            ptr = None

    disjuncts.reverse()
    return disjuncts

def step0_minterms(term):
    term = term.normalize()
    disjuncts = disjunctlist(term)
    variables = term.variables
    newdisjuncts = []
    for disjunct in disjuncts:
        L = [disjunct]
        for var in variables:
            L2 = []
            for tmp in L:
                if var not in tmp:
                    L2.append(tmp&var)
                    L2.append(tmp&~var)
                else:
                    L2.append(tmp)

            L = L2

        newdisjuncts += L

    return newdisjuncts
