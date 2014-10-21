# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from .logic import Atomic, Bool, And, Or, Not, QuineMcCluskey

class OpCodes(object):
    def __init__(self):
        self.table = [dict()]
        self.ops = set()
    def add_codes(self, colname, ops):
        d = self.current
        d.setdefault(colname, [])
        d[colname].append(ops)
        self.ops.add(ops)
    def __iter__(self):
        for i, row in enumerate(self.table):
            for col, ops in row.items():
                for op in ops:
                    yield i, col, op
    def new_row(self):
        self.table.append({})
    def add_row(self, row):
        self.table.append(row)
    def merge_row(self, row):
        for colname, opcodes in row.items():
            for ops in opcodes:
                self.add_codes(colname, ops)
    @property
    def current(self):
        return self.table[-1]

    @current.setter
    def current(self, row):
        self.table[-1] = row

class Expr(Bool):
    def columns(self):
        variables = filter(lambda x:isinstance(x, BinOp), self.variables)
        colnames = list({v.colname for v in variables})
        colnames.sort()
        colids = [(colname, colid) for colid, colname in enumerate(colnames)]
        return colids
    def col_list(self):
        variables = filter(lambda x:isinstance(x, BinOp), self.variables)
        colnames = list({v.colname for v in variables})
        colnames.sort()
        if not colnames:
            return []
        res = [-1] * (max(colnames)+1)
        for colid, colval in enumerate(colnames):
            res[colval] = colid
        return res
    def __and__(self, other):
        return qAnd(self, other)
    def __or__(self, other):
        return qOr(self, other)
    def __invert__(self):
        return qNot(self)
    def minimalize(self):
        expr = self.normalize()
        obj = QuineMcCluskey(expr)
        expr = obj.compute()
        return expr

class qAtomic(Expr, Atomic):
    def _construct(self):
        eng = OpCodes()
        eng.add_codes(self.colname, self.ops)
        return eng

class Top(qAtomic):
    def __init__(self, name='T'):
        self.name = name
    def _construct(self):
        eng = OpCodes()
        return eng

class Column(object):
    def __init__(self, name):
        self.colname = name
    def contains(self, other):
        return BinOp('in',  self.colname, other)
    def notcontains(self, other):
        return BinOp('nin',  self.colname, other)
    def __eq__(self, other):
        return BinOp('=',  self.colname, other)
    def __ne__(self, other):
        return BinOp('!=', self.colname, other)
    def __lt__(self, other):
        return BinOp('<',  self.colname, other)
    def __le__(self, other):
        return BinOp('<=', self.colname, other)
    def __gt__(self, other):
        return BinOp('>',  self.colname, other)
    def __ge__(self, other):
        return BinOp('>=', self.colname, other)

class BinOp(qAtomic):
    def __init__(self, op, colname, queryword):
        self.name = "col_{} {} '{}'".format(colname, op, queryword)
        self.colname = colname
        self.ops = (op, queryword)
        self.args = set([self])

class qNot(Expr, Not):
    @property
    def colname(self):
        return self.child.colname
    def invert(self, op):
        if op=='=':
            return '!='
        elif op=='!=':
            return '='
        elif op=='>':
            return '<='
        elif op=='<':
            return '>='
        elif op=='<=':
            return '>'
        elif op=='>=':
            return '<'
        elif op=='in':
            return 'nin'
        elif op=='nin':
            return 'in'
    def _construct(self):
        child = self.child
        eng0 = OpCodes()
        eng1 = child._construct()
        for colname, opcodes in eng1.current():
            for ops in opcodes:
                nops = (self.invert(ops[0]), ops[1])
                eng0.add_codes(colname, nops)

        return eng0

class qAnd(Expr, And):
    def _construct(self):
        children = self.children()
        children.sort(key=lambda x: list(x.variables)[0].colname)
        eng = OpCodes()
        for child in children:
            e0 = child._construct()
            eng.merge_row(e0.current)

        return eng

class qOr(Expr, Or):
    def _construct(self):
        children = self.children()
        eng = OpCodes()
        for child in children:
            e0 = child._construct()
            eng.merge_row(e0.current)
            eng.new_row()

        return eng

