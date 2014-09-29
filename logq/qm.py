# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

class Bool(object):
    @classmethod
    def create(cls, string):
        u"""
        >>> a, b, c = Bool.create('abc')
        >>> a | b
        a | b
        """
        return [Atomic(c) for c in string]

    def __init__(self, *args):
        self.args = args

    @property
    def atomic(self):
        return isinstance(self, Atomic)
    def expand(self):
        return self
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return self.name == other
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

class Atomic(Bool):
    def __init__(self, *args):
        self.args = args
        self.name = self.args[0]

class UnaryTerm(Bool):
    op = ''
    def __init__(self, *args):
        self.args = args
        self.name = '{} {}'.format(self.op, args[0])
    def __contains__(self, other):
        return other in self.args

class BinaryTerm(Bool):
    op = ''
    def __init__(self, *args):
        self.args = args
        self.fst = args[0]
        self.snd = args[1]
        self.name = '{} {} {}'.format(self.fst, self.op, self.snd)
    def __contains__(self, other):
        return other in self.args
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.fst == other.fst and self.snd == other.snd) or (self.fst == other.snd and self.snd == other.fst)
        else:
            return False

class And(BinaryTerm):
    op = '&'
    def expand(self):
        """
        (A + B) C
        -> AC + BC

        A (B + C)
        -> A B + A C

        (A + B) (C + D)
        -> AC + AD + BC + BD
        """
        # a & a -> a
        if self.fst == self.snd:
            return self.fst
        # a & (a | c) -> a
        if isinstance(self.snd, Or) and self.fst in self.snd:
            return self.fst
        if isinstance(self.fst, Or) and self.snd in self.fst:
            return self.snd

        args0 = self.args[0].expand()
        args1 = self.args[1].expand()
        if args0 == args1:
            return args0

        if isinstance(args0, Or):
            return Or(And(args0.fst, args1).expand(),
                      And(args0.snd, args1).expand())
        elif isinstance(args1, Or):
            return Or(And(args0, args1.fst).expand(),
                      And(args0, args1.snd).expand())
        else:
            return self

class Or(BinaryTerm):
    op = '|'
    def expand(self):
        # a | a -> a
        if self.fst == self.snd:
            return self.fst
        # a | (a & c) -> a
        if isinstance(self.snd, And) and self.fst in self.snd:
            return self.fst
        if isinstance(self.fst, And) and self.snd in self.fst:
            return self.snd

        return self

class Not(UnaryTerm):
    op = '~'
