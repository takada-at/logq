# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
"""
EngineFactory
===============
"""

from collections import deque
from collections import namedtuple
from .engine import Engine

def compile_query(expr):
    factory = EngineFactory()
    return factory.compile_query(expr)

class PyEngine(object):
    def __init__(self, start, success, fail, exprs, expr_table, success_table, fail_table):
        self.start = start
        self.success = success
        self.fail = fail
        self.expr_table = expr_table
        self.success_table = success_table
        self.fail_table = fail_table
        self.exprs = exprs
        self.cols = list(range(len(self.expr_table[0])))
        self.reset()
    def reset(self):
        self.state = self.start
        self.is_success = False
        self.is_fail = False
    def format_op(self, op):
        return "{}{}".format(*op)
    def format(self):
        cols = [""] + map(str, self.cols)
        res = ["\t".join(cols)]
        for st, row in enumerate(self.expr_table):
            show = [str(st)]
            for colid, val in enumerate(row):
                if val==0:
                    s = ''
                else:
                    expr  = "[{}]".format(colid) + self.format_op(self.exprs[val])
                    succ  = self.success_table[st][colid]
                    fail  = self.fail_table[st][colid]
                    if succ==self.success:
                        succ = '[{}]'.format(succ)
                    if fail==self.fail:
                        fail = '[{}]'.format(fail)

                    s = ",".join((expr, str(succ), str(fail)))

                show.append(s)

            res.append("\t".join(show))

        return "\n".join(res)
    def execute_op(self, op, arg, val):
        if op=='=':
            return arg==val
        elif op=='!=':
            return arg!=val
        elif op=='>=':
            return val>=arg
        elif op=='<=':
            return val<=arg
        elif op=='>':
            return val>arg
        elif op=='<':
            return val<arg
        elif op=='in':
            return arg in val
        elif op=='nin':
            return arg not in val
    def transition(self, col, val):
        state = self.state
        while True:
            opid = self.expr_table[self.state][col]
            if opid:
                op, arg = self.exprs[opid]
                res = self.execute_op(op, arg, val)
                if res:
                    self.state = self.success_table[self.state][col]
                    self.is_success = self.state == self.success
                    if self.state<=state: break
                else:
                    self.state = self.fail_table[self.state][col]
                    self.is_fail = self.state == self.fail
            else:
                return None

            state = self.state

        return True

ExprNode = namedtuple('ExprNode', 'col row index id')
class ExprList():
    def __init__(self, state, excludes=None):
        if excludes is None: excludes = set()
        self.excludes = excludes
        self.state = state
        self.startnode = None
        self.exprlist = dict()
        self.statecache = dict()
    def maxrowstate(self):
        return max(self.exprlist.keys())
    def set_start(self, rowstate, expr):
        self.statecache[rowstate, expr.index] = self.state
        self.startnode = (rowstate, expr)
    def new_state(self, rowstate, index):
        if (rowstate, index) in self.statecache:
            return self.statecache[rowstate, index]

        self.state += 1
        while self.state in self.excludes:
            self.state += 1

        self.statecache[rowstate, index] = self.state
        return self.state
    def findright(self, rowstate, expr):
        """
        状態が同じで、行が同じものがあるかどうかを探す。
        """
        if rowstate not in self.exprlist:
            return None

        row = expr.row
        key = (expr.col, expr.index)
        for nexpr in self.exprlist[rowstate]:
            if nexpr.row==row and (nexpr.col, nexpr.index) > key:
                return nexpr

        return None
    def nextexpr(self, rowstate, expr):
        if rowstate not in self.exprlist:
            return None

        k = (expr.col, expr.row, expr.index)
        for nexpr in self.exprlist[rowstate]:
            if (nexpr.col, nexpr.row, nexpr.index) > k:
                return nexpr

        return None

    def add(self, rowstate, expr):
        if not self.exprlist:
            self.set_start(rowstate, expr)
        if rowstate not in self.exprlist:
            self.exprlist[rowstate] = []

        self.exprlist[rowstate].append(expr)

class EngineFactory():
    engineclass = Engine
    START = 0
    SUCCESS = 1
    FAIL = 2
    @classmethod
    def set_engineclass(cls, class_):
        cls.engineclass = class_
    def fexpr(self, expr):
        for k, v in self.opids.items():
            if v==expr.id:
                return k
    def compile_query(self, expr):
        expr = expr.minimalize()
        colids = expr.columns()
        opcodes = expr._construct()
        return self.construct(opcodes, colids)
    def dict2table(self, exprlist, colids, dic):
        res = []
        last = max(self.FAIL, exprlist.state)
        for i in range(last+1):
            res.append([0 for col in colids])

        for col, st in dic.keys():
            res[st][col] = dic[col, st]

        return res
    def construct(self, opcodes, colids):
        self.expr_table = dict()
        self.success_table = dict()
        self.fail_table = dict()
        self.opids = dict()
        cnt = 1
        for op in opcodes.ops:
            if op not in self.opids:
                self.opids[op] = cnt
                cnt += 1

        start = self.START
        success = self.SUCCESS
        fail = self.FAIL
        exprlist = ExprList(0, excludes={1,2})
        self._construct_exprlist(opcodes.table, colids, exprlist)
        self._construct_table(exprlist, start, success, fail)
        expr_table = self.dict2table(exprlist, colids, self.expr_table)
        exprs = self.opids.items()
        exprs.sort(key=lambda x:x[1])
        exprs = [None]+[k for k, v in exprs]
        success_table = self.dict2table(exprlist, colids, self.success_table)
        fail_table = self.dict2table(exprlist, colids, self.fail_table)
        klass = self.engineclass
        return klass(start, success, fail, exprs, expr_table, success_table, fail_table)
    def _construct_exprlist(self, table, colids, exprlist):
        table = filter(None, table)
        rowstates = range(0, 2**len(table)+1)
        rowstates.reverse()
        for rowstate in rowstates:
            for colname, colid in colids:
                index = 0
                for rowid, row in enumerate(table):
                    if ((rowstate >> rowid) & 1)==0: continue
                    if colname not in row: continue
                    exprs = row[colname]
                    for ops in exprs:
                        opid = self.opids[ops]
                        expr = ExprNode(colid, rowid, index, opid)
                        exprlist.add(rowstate, expr)
                        index += 1

    def _construct_table(self, exprlist, start, success, fail):
        if not exprlist: return
        rowstate, expr = exprlist.startnode
        que = deque([(start, rowstate, expr)])
        while que:
            state, rowstate, expr = que.popleft()
            col, row, index, opid = expr
            self.expr_table[col, state] = opid
            # 失敗の場合
            newrowstate = rowstate - (1<<row)
            nexpr = exprlist.nextexpr(newrowstate, expr)
            if nexpr:
                nstate = exprlist.new_state(newrowstate, nexpr.index)
                self.fail_table[col, state] = nstate
                que.append((nstate, newrowstate, nexpr))
            else:
                # 次がないので終了
                self.fail_table[col, state] = fail

            # 成功の場合
            right = exprlist.findright(rowstate, expr)
            if right:
                # 次に評価する式を探す
                nexpr = exprlist.nextexpr(rowstate, expr)
                nstate = exprlist.new_state(rowstate, nexpr.index)
                self.success_table[col, state] = nstate
                que.append((nstate, rowstate, nexpr))
            else:
                # この行にこれ以上式がないので成功すれば終了
                self.success_table[col, state] = success
