# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import operator

def pairs(L):
    leng = len(L)
    for idx0 in range(leng-1):
        for idx1 in range(idx0+1, leng):
            yield idx0, idx1, L[idx0], L[idx1]

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
        for idx0, idx1, x, y in pairs(children):
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

class QuineMcCluskey(object):
    u"""
    c.f. http://en.wikipedia.org/wiki/Quine%E2%80%93McCluskey_algorithm
    """
    def __init__(self, term):
        self.term = term.normalize()
        variables = list(term.variables)
        variables.sort(lambda x,y: cmp(x.name, y.name))
        self.variables = variables
    def compute(self):
        # 最小項標準形への変換
        minterns = self.step0_minterms()
        # 主項をえる
        prime_implicants = self.step1_prime_implicants(bins)
        # 必須項をえる
        return self.step2_essential_prime_implicants(prime_implicants)
    def step0_minterms(self):
        """
        最小項標準形への変換
        """
        def addvar(var, L):
            res = []
            for term in L:
                if var not in term and ~var not in term:
                    res += [term+[var], term+[~var]]
                else:
                    res.append(term)

            return res

        variables = self.variables
        disjuncts = self.term.children()
        newdisjuncts = []
        for disjunct in disjuncts:
            L = [disjunct.children()]
            for var in variables:
                L = addvar(var, L)

            newdisjuncts += L

        return self._normalize_terms(newdisjuncts)
    def step1_prime_implicants(self, terms):
        """
        主項を見つける
        """
        trees = [MergeTree({idx}, term) for idx, term in enumerate(terms)]
        merged, _ = self._merge(trees)
        primes = []
        while merged:
            merged, marked = self._merge(merged)
            primes += marked

        return primes
    def step2_essential_prime_implicants(self, implicants):
        """
        必須項を見つける

        http://en.wikipedia.org/wiki/Petrick%27s_method
        """
        table = dict()
        names = dict()
        name2t= dict()
        c = 0
        for term in implicants:
            # naming terms
            name = "p{}".format(c)
            names[id(term)] = name
            name2t[name] = term
            c+=1
            for id_ in term.ids:
                table.setdefault(id_, set())
                table[id_].add(term)

        essentials = []
        variables = self.variables
        functions = []
        for id_, terms in table.items():
            if len(terms)==1:
                essentials += terms
                continue
            else:
                forms = [Atomic(names[id(term)]) for term in terms]
                boolean = reduce(operator.or_, forms)
                # ex. p0 | p1
                functions.append(boolean)

        # ex. (p0 | p1) & (p2 | p3)
        sums = reduce(operator.and_, functions)
        sums = sums.normalize()
        ranks = []
        for disjunct in sums.children():
            # sort by (1. num of prime implicants, 2. num of atomics of each prime implicants)
            rank = sum(len(name2t[t.name]) for t in disjunct.children())
            ranks.append(len(disjunct.children()), rank, disjunct)

        ranks.sort(key=lambda x: (x[0],x[1]))
        essentials += [name2t[t.name] for t in ranks[0][2].children()]
        return essentials

    def _normalize_terms(self, terms):
        variables = self.variables
        cache = set()
        res   = []
        for disjunct in terms:
            # convert to 1/0
            disjunct = tuple(1 if v in disjunct else 0 for v in variables)
            # delete non unique terms
            if disjunct in cache:
                continue
            cache.add(disjunct)
            res.append(disjunct)

        return res
    def _merge(self, terms):
        mergedterms = set()
        pairl = []
        for i, j, term0, term1 in pairs(terms):
            merged = term0.try_merge(term1)
            if merged:
                mergedterms.add(i)
                mergedterms.add(j)
                pairl.append(merged)

        marked = [term for i, term in enumerate(terms) if i not in mergedterms]
        return (pairl, marked)

class MergeTree(object):
    CHAR = '_'
    def __init__(self, ids, expr):
        self.ids   = ids  # {0,}
        self.expr  = expr # [0, 1, 1]
        self._len = len([c for c in expr if c!= self.CHAR])
    def __len__(self):
        return self._len
    def boolean(self, variables):
        res = []
        for i, var in enumerate(variables):
            if self.expr[i]==0: res.add(~var)
            elif self.expr[i]==1: res.add(var)

        return reduce(operator.and_, res)
    def try_merge(self, other):
        distance, merged = self._merge(self.expr, other.expr)
        if distance<=1:
            ids  = self.ids | other.ids
            return self.__class__(ids, tuple(merged))
        else:
            return None
    def __repr__(self):
        val = "".join(map(unicode, self.expr))
        idx = ", ".join(map(unicode, self.ids))
        return "m({})={}".format(idx, val)
    def _merge(self, x,y):
        merged = list(x[:])
        distance = 0
        c = self.CHAR
        for i in range(len(x)):
            if x[i]!=y[i]:
                merged[i]=c
                distance += 1

        return (distance, merged)

