# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

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

class And(BinaryTerm):
    op = '&'
    def normalize(self):
        if self._mark: return self
        # a & a -> a
        if self.fst == self.snd:
            return self.fst.normalize()
        # a & (a | c) -> a
        if isinstance(self.snd, Or) and self.fst in self.snd:
            return self.fst.normalize()
        # (a | b) & a -> a
        if isinstance(self.fst, Or) and self.snd in self.fst:
            return self.snd.normalize()

        args0 = self.fst
        args1 = self.snd
        # (A | B) & C -> A & C | B & C
        if isinstance(args0, Or):
            left   = (args0.fst & args1).normalize()
            right  = (args0.snd & args1).normalize()
            return (left | right).normalize()
        # A & (B | C) -> A & B | A & C
        elif isinstance(args1, Or):
            left   = (args0 & args1.fst).normalize()
            right  = (args0 & args1.snd).normalize()
            return (left | right).normalize()
        # (A & B) & C -> A & (B & C)
        if isinstance(args0, And):
            left = args0.fst
            right = (args0.snd & args1)
            # try A & (B & C)
            right2 = right.normalize()
            if right != right2:
                left2 = left.normalize()
                return (left2 & right2).normalize()
            # try (A & C) & B
            left = args0.fst & args1
            left2 = left.normalize()
            if left != left2:
                right2 = args0.snd
                return (left2 & right2).normalize()

        # A & (B & C) -> (A & B) & C
        if isinstance(args1, And):
            left = (args0 & args1.fst).normalize()
            right = args1.snd.normalize()
            return (left & right).normalize()

        left2 = args0.normalize()
        right2 = args1.normalize()
        if left2!=args0 or right2!=args1:
            return (left2 & right2).normalize()

        self._mark = True
        return self

class Or(BinaryTerm):
    op = '|'
    def normalize(self):
        if self._mark: return self
        # a | a -> a
        if self.fst == self.snd:
            return self.fst.normalize()
        # a | (a & c) -> a
        if isinstance(self.snd, And) and self.fst in self.snd:
            return self.fst.normalize()
        # (a & c) | a -> a
        if isinstance(self.fst, And) and self.snd in self.fst:
            return self.snd.normalize()

        args0 = self.fst
        args1 = self.snd
        # (A | B) | C
        if isinstance(args0, Or):
            left = args0.fst
            right = (args0.snd | args1)
            # try A | (B | C)
            right2 = right.normalize()
            if right != right2:
                left2 = left.normalize()
                return (left2 | right2).normalize()
            # try (A | C) | B
            left = args0.fst | args1
            left2 = left.normalize()
            if left != left2:
                right2 = args0.snd
                return (left2 | right2).normalize()

        # A | (B | C) -> (A | B) | C
        if isinstance(args1, Or):
            left = (args0 | args1.fst).normalize()
            right = args1.snd.normalize()
            return (left  | right).normalize()

        left2 = args0.normalize()
        right2 = args1.normalize()
        if left2!=args0 or right2!=args1:
            return (left2 | right2).normalize()

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
