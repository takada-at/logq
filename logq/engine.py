# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
from collections import Counter, defaultdict
from itertools import combinations
from .logic import Atomic, Bool, And, Or, Not

class CsvParser(object):
    """
    サンプル実装のパーサー
    """
    def __init__(self, fileobj, engine):
        self.fileobj = fileobj
        self.engine  = engine
    def read(self):
        self.newline()
        string = self.fileobj.read()
        for c in string:
            self.state = self.readc(c, self.state)
            if self.state==15:
                yield self.vals

            self.newline()
    def newline(self):
        self.col = 0
        self.state = 0
        self.buffer = ''
        self.engine.newline()
        self.vals = []
    def readc(self, c, state):
        if c=='"':
            if state==0:
                return 1
            elif state==1:
                return 0
        elif c==',':
            if state==1: self.buffer+=c; return 1
            val = self.buffer
            self.buffer = ''
            self.vals.append(val)
            self.col += 1
            if state!=4 and state!=5:
                res = engine.match(self.col, self.buffer)
                if res == Engine.FAIL: return 5
                elif res == Engine.SUCCESS: return 4
        elif c=='\n':
            if state==1: self.buffer+=c; return 1
            else:
                val = self.buffer
                if state!=4 and state!=5:
                    res = engine.match(self.col, self.buffer)
                    if res == Engine.FAIL: state=5
                    elif res == Engine.SUCCESS: state=4

                return state + 10
        else:
            self.buffer += c
            return state

class Engine(object):
    NORMAL = 0
    ACCEPT = 1
    FAIL = 2
    @classmethod
    def construct(cls, expr):
        expr.normalize()
        opcodes = expr._construct()
        return cls(opcodes)

    def __init__(self, opcodes):
        self.opcodes = opcodes
    def newline(self):
        self._flag = dict():
        for i, row in enumerate(self.opcodes.table):
            self._flag[i] = {k: 0 for k in row.keys()}
    def match(self, colname, val):
        res = self._flag
        for i, row in enumerate(self.opcodes.table):
            opcodes = row[colname]
            if all(self.execute_op(op, arg, val) for op, arg in opcodes):
                del(res[i][colname])
                if not res[i]: return self.ACCEPT
            else:
                del(res[i][colname])
                if not res[i]:
                    del(res[i])
                    if not res: return self.FAIL

        return self.NORMAL
    def execute_op(self, op, arg, val):
        if op=="=":
            return arg==val

class OpCodes(object):
    def __init__(self):
        self.table = [dict()]
    def add_codes(self, colname, ops):
        d = self.current
        d.setdefault(colname, [])
        d[colname].append(ops)
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

class BaseBool(Bool):
    def __and__(self, other):
        return qAnd(self, other)
    def __or__(self, other):
        return qOr(self, other)
    def __invert__(self):
        return qNot(self)
    def compile(self):
        engine = Engine.construct(self)
        return engine

class Expr(BaseBool, Atomic):
    def _construct(self):
        eng = OpCodes()
        eng.add_codes(self.colname, self.ops)
        return eng

class Column(object):
    def __init__(self, name):
        self.colname = name
    def __eq__(self, other):
        return StringEq(self.colname, other)

class StringEq(Expr):
    def __init__(self, colname, queryword):
        self.name = "col_{} = '{}'".format(colname, queryword)
        self.colname = colname
        self.ops = ('=', queryword)
        self.args = set([self])

class qNot(BaseBool, Not):
    @property
    def colname(self):
        return self.child.colname
    def invert(self, op):
        if op=='=':
            return '!='
        elif op=='>':
            return '<='
        elif op=='<':
            return '>='
        elif op=='<=':
            return '>'
        elif op=='>=':
            return '<'
    def _construct(self):
        child = self.child
        eng0 = OpCodes()
        eng1 = child._construct(factory)
        for colname, opcodes in eng1.current():
            for ops in opcodes:
                nops = (self.invert(ops[0]), ops[1])
                eng0.add_codes(colname, nops)

        return eng0

class qAnd(BaseBool, And):
    def _construct(self):
        children = self.children()
        children.sort(key=lambda x: list(x.variables)[0].colname)
        eng = OpCodes()
        for child in children:
            e0 = child._construct()
            eng.merge_row(e0.current)

        return eng

class qOr(BaseBool, Or):
    def _construct(self):
        children = self.children()
        eng = OpCodes()
        for child in children:
            e0 = child._construct()
            eng.merge_row(e0.current)
            eng.new_row()

        return eng

