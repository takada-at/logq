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
            return var<=arg
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
Position = namedtuple('Position', 'rowstate row col idxincol opid')
class PosList():
    def __init__(self, state, excludes=None):
        if excludes is None: excludes = set()
        self.excludes = excludes
        self.posdict = dict()
        self.state = state
        self.poslist = []
        self.statecache = dict()
    def set_start(self, pos):
        self.statecache[pos.rowstate, pos.idxincol] = self.state
    def new_state(self, pos):
        if (pos.rowstate, pos.idxincol) in self.statecache:
            return self.statecache[pos.rowstate, pos.idxincol]

        self.state += 1
        while self.state in self.excludes:
            self.state += 1

        self.statecache[pos.rowstate, pos.idxincol] = self.state
        return self.state
    def state(self, pos):
        return self.posdict[pos]
    def findright(self, pos):
        """
        状態が同じで、行が同じものがあるかどうかを探す。
        """
        row = pos.row
        rowstate = pos.rowstate
        key = (pos.col, pos.idxincol)
        for npos in self:
            if npos.rowstate==rowstate and npos.row==row \
                    and (npos.col, npos.idxincol) > key:
                return npos

        return None
    def successstate(self, pos):
        """
        成功した場合

        行の状態は同じでこれよりあとの行か、次の列
        """
        idxincol = pos.idxincol
        rowstate = pos.rowstate
        k = (pos.col, idxincol)
        for pos2 in self:
            if pos2.rowstate != rowstate: continue
            if (pos2.col, pos2.idxincol) > k: 
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
        if pos in self.posdict: return
        if not self.poslist:
            self.set_start(pos)

        self.poslist.append(pos)

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
        last = max(self.FAIL, poslist.state)
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
        poslist = PosList(0, excludes={1,2})
        self._construct_poslist(opcodes.table, colids, poslist)
        self._construct_table(poslist, start, success, fail)
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
                idxincol = 0
                for rowid, row in enumerate(table):
                    if ((rowstate >> rowid) & 1)==0: continue
                    if colname not in row: continue
                    exprs = row[colname]
                    for ops in exprs:
                        opid = self.opids[ops]
                        pos = Position(rowstate, rowid, colid, idxincol, opid)
                        poslist.add(pos)
                        idxincol += 1

    def _construct_table(self, poslist, start, success, fail):
        if not poslist: return
        que = deque([(start, poslist[0])])
        while que:
            state, pos = que.popleft()
            rowstate, rowid, col, idxincol, opid = pos
            self.expr_table[col, state] = opid
            # 失敗の場合
            npos = poslist.failstate(pos)
            if npos:
                nstate = poslist.new_state(npos)
                self.fail_table[col, state] = nstate
                que.append((nstate, npos))
            else:
                # 次がないので終了
                self.fail_table[col, state] = fail

            # 成功の場合
            right = poslist.findright(pos)
            if not right:
                # この行にこれ以上式がないので成功すれば終了
                self.success_table[col, state] = success
            else:
                # 次に評価する式を探す
                npos = poslist.successstate(pos)
                if npos:
                    nstate = poslist.new_state(npos)
                    self.success_table[col, state] = nstate
                    que.append((nstate, npos))
                else:
                    self.success_table[col, state] = success
