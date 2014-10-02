# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

class Engine():
    def __init__(self, start, success, fail, action_table, success_table, fail_table, exprs):
        self.start = start
        self.success = success
        self.fail = fail
        self.action_table = action_table
        self.success_table = success_table
        self.fail_table = fail_table
        self.exprs = exprs

class PosList():
    def __init__(self, state):
        self.posdict = dict()
        self._state = state
        self.poslist = []
    def state(self, pos):
        return self.posdict[pos]
    def nextrow(self, idx, pos):
        rowid = pos[1]
        rowstate = pos[0] - (1<<rowid)
        idx += 1
        while idx < len(self.poslist):
            n = self.poslist[idx]
            if pos[0]==rowstate:
                return n
            idx += 1

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

class EngineFactory():
    def dict2table(self, poslist, cols, dic):
        res = []
        last = poslist.state(poslist[-1])
        for i in range(last+1):
            res.append([0 for col in cols])

        for pos in poslist:
            st = poslist.state(pos)
            col = pos[2]
            res[st][col] = dic[st]

        return res

    def construct(self, opcodes, cols):
        self.action_table = dict()
        self.success_table = dict()
        self.fail_table = dict()
        self.opids = dict()
        self.opids[None, None] = 0
        cnt = 1
        for op in opcodes.ops:
            if op not in self.opids:
                self.opids[op] = cnt
                cnt += 1

        start = 0
        success = 1
        fail = 2
        poslist = PosList(0)
        self._construct_poslist(opcodes.table, cols, poslist)
        for idx, pos in enumerate(poslist):
            state = poslist.state(pos)
            rowstate, rowid, col, oppos, opid = pos
            self.action_table[state] = opid
            if idx==len(poslist)-1:
                self.success_table[state] = success
                self.fail_table[state] = fail
                break

            nextrow = poslist.nextrow(idx, pos)
            if nextrow:
                self.fail_table[state] = poslist.state(nextrow)
            else:
                self.fail_table[state] = fail

            pos2 = poslist[idx+1]
            state2 = poslist.state(pos2)
            rowstate2, rowid2, col2, oppos2, _  = pos2
            if rowstate==rowstate2 and rowid==rowid2:
                self.success_table[state] = state2
            else:
                self.success_table[state] = success

        action_table = self.dict2table(poslist, cols, self.action_table)
        exprs = self.opids.items()
        exprs.sort()
        exprs = [k for k, v in exprs]
        success_table = self.dict2table(poslist, cols, self.success_table)
        fail_table = self.dict2table(poslist, cols, self. fail_table)
        return Engine(start, success, fail, action_table, success_table,
                      fail_table, exprs)

    def _construct_poslist(self, table, cols, poslist):
        rowstates = range(1, 2**len(table))
        rowstates.reverse()
        for rowstate in rowstates:
            for col in cols:
                flag = False
                for rowid, row in enumerate(table):
                    if ((rowstate >> rowid) & 1)==0: continue
                    if col not in row: continue
                    flag = True
                    exprs = row[col]
                    for oppos, ops in enumerate(exprs):
                        opid = self.opids[ops]
                        pos = (rowstate, rowid, col, oppos, opid)
                        poslist.add(pos)

                if flag:
                    # go next column
                    pos = (rowstate, rowid, col, oppos+1, 0)
                    poslist.add(pos)


