# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
"""
EngineFactory
===============
"""

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
        return " {}{}".format(*op)
    def format(self):
        cols = [""] + map(str, self.cols)
        res = ["\t".join(cols)]
        for st, row in enumerate(self.expr_table):
            show = [str(st)]
            for colid, val in enumerate(row):
                if val==0:
                    s = ''
                else:
                    expr  = self.format_op(self.exprs[val])
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
    def transition(self, col, val):
        while True:
            opid = self.expr_table[self.state][col]
            if opid:
                op, arg = self.exprs[opid]
                res = self.execute_op(op, arg, val)
                if res:
                    self.state = self.success_table[self.state][col]
                    self.is_success = self.state == self.success
                else:
                    self.state = self.fail_table[self.state][col]
                    self.is_fail = self.state == self.fail
            else:
                return None

class PosList():
    def __init__(self, state, excludes=None):
        if excludes is None: excludes = set()
        self.excludes = excludes
        self.posdict = dict()
        self._state = state
        self.poslist = []
    def state(self, pos):
        return self.posdict[pos]
    def findright(self, idx, pos):
        """
        状態が同じで、行が同じものがあるかどうかを探す。
        """
        rowstate = pos[0]
        rowid = pos[1]
        for npos in self[idx+1:]:
            if npos[0]==rowstate and npos[1]==rowid:
                return npos

        return None
    def successstate(self, idx, pos):
        """
        成功した場合

        行の状態は同じでこれよりあとの行か、次の列
        """
        rowstate = pos[0]
        k = (pos[2], pos[1]) # col, row
        for pos2 in self[idx+1:]:
            if pos2[0] == rowstate and (pos2[2], pos2[1]) >= k:
                return pos2

        return None

    def failstate(self, pos):
        """
        失敗した場合

        行の状態を失敗にして、同じ列でこれよりあとの行か、次の列を検索
        """
        rowid = pos[1]
        rowstate = pos[0] - (1<<rowid)
        k = (pos[2], rowid) # col, row
        for pos2 in self:
            if pos2[0]==rowstate and (pos2[2], pos2[1]) > k:
                return pos2

        return None
    def __getitem__(self, idx):
        return self.poslist[idx]
    def __len__(self):
        return len(self.poslist)
    def __iter__(self):
        return iter(self.poslist)
    def add(self, pos):
        self.poslist.append(pos)
        self.posdict[pos] = self._state
        self._state += 1
        while self._state in self.excludes:
            self._state += 1

class EngineFactory():
    engineclass = Engine
    START = 0
    SUCCESS = 1
    FAIL = 2
    @classmethod
    def set_engineclass(cls, class_):
        cls.engineclass = class_
    def compile_query(self, expr):
        expr = expr.minimalize()
        colids = expr.columns()
        opcodes = expr._construct()
        return self.construct(opcodes, colids)
    def dict2table(self, poslist, colids, dic):
        res = []
        last = max(poslist.state(poslist[-1]), self.FAIL)
        for i in range(last+1):
            res.append([0 for col in colids])

        for pos in poslist:
            st = poslist.state(pos)
            col = pos[2]
            res[st][col] = dic[st]

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
        poslist = PosList(0, excludes={1,2})
        self._construct_poslist(opcodes.table, colids, poslist)
        for idx, pos in enumerate(poslist):
            state = poslist.state(pos)
            rowstate, rowid, col, oppos, opid = pos
            self.expr_table[state] = opid
            if idx==len(poslist)-1:
                self.success_table[state] = success
                self.fail_table[state] = fail
                break

            nextrow = poslist.failstate(pos)
            if nextrow:
                self.fail_table[state] = poslist.state(nextrow)
            else:
                self.fail_table[state] = fail

            # この行にこれ以上式がないならば成功すれば終了
            right = poslist.findright(idx, pos)
            if not right:
                self.success_table[state] = success
            else:
                # 次に評価する式を探す
                npos = poslist.successstate(idx, pos)
                if npos:
                    self.success_table[state] = poslist.state(npos)
                else:
                    self.success_table[state] = success

        expr_table = self.dict2table(poslist, colids, self.expr_table)
        exprs = self.opids.items()
        exprs.sort(key=lambda x:x[1])
        exprs = [None]+[k for k, v in exprs]
        success_table = self.dict2table(poslist, colids, self.success_table)
        fail_table = self.dict2table(poslist, colids, self.fail_table)
        klass = self.engineclass
        return klass(start, success, fail, exprs, expr_table, success_table, fail_table)
    def _construct_poslist(self, table, colids, poslist):
        rowstates = range(0, 2**len(table)+1)
        rowstates.reverse()
        for rowstate in rowstates:
            for colname, colid in colids:
                for rowid, row in enumerate(table):
                    if ((rowstate >> rowid) & 1)==0: continue
                    if colname not in row: continue
                    exprs = row[colname]
                    for oppos, ops in enumerate(exprs):
                        opid = self.opids[ops]
                        pos = (rowstate, rowid, colid, oppos, opid)
                        poslist.add(pos)
