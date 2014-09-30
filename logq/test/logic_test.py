# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import logic as qm

def test_Bool():
    a, b, c, d = qm.Bool.create('abcd')
    r = a | b
    assert r.name == 'a | b'

    r = a & b & c & (d | a)
    assert {a, b, c, d} == r.variables

    r = (b & c) & d
    assert [b, c, d] == r.children()

    r = a | a & c
    assert [a] == r.filter_children(r.children())

def test_normalize():
    a, b, c, d = qm.Bool.create('abcd')
    r = a | b
    assert r.normalize()==r

    r = (a | b) & c
    assert r.normalize() == a & c | b & c
    assert r.normalize().name == 'a & c | b & c'

    r = a & (b | c)
    assert r.normalize() == a & b | a & c
    assert r.normalize().name == 'a & b | a & c'

    r = a & (a | c)
    assert r.normalize() == a
    assert r.normalize().name == 'a'

    r = (a | b) & (a | c)
    #->a & (a|c) | b & (a|c)
    #->a | (b & a | a & c)
    #->a | b & c
    assert r.normalize() == a | b & c

    r = ~ (a & b)
    # -> ~a | ~b
    assert r.normalize() == ~a | ~b
    assert r.normalize().name == '~a | ~b'

    r = ~((a | b) & ~c)
    # -> ~(a | b) | ~~c
    # -> ~a & ~b | c
    r2 = r.normalize()
    assert r2 == ~a & ~b | c
    assert r2.name == '~a & ~b | c'

    r = ~(a | b & c)
    # -> ~a & ~(b & c)
    # -> ~a & (~b | ~c)
    # -> ~a & ~b | ~a & ~c
    assert r.normalize() == ~a & ~b | ~a & ~c

    r = (~(a | b & c) & d)
    # -> (~a & ~(b & c)) & d
    # -> (~a & (~b | ~c)) & d
    # -> (~a & ~b | ~a & ~c) & d
    # -> ~a & ~b & d | ~a & ~c & d
    r2 = r.normalize()
    assert r2 == ~a & ~b & d | ~a & ~c & d
    assert r2.name == '(~a & ~b) & d | (~a & ~c) & d'

    r = a | b | c | a
    r2 = r.normalize()
    assert r2 == a | b | c

    r = a | b | c | d & a
    r2 = r.normalize()
    assert r2 == a | b | c

    r = a & b & c & (d | a)
    r2 = r.normalize()
    assert r2 == a & b & c

def test_step0_minterms():
    a, b, c, d = qm.Bool.create('abcd')
    term = a & b | b & c
    term = term.normalize()
    assert a & b | b & c == term
    disjuncts = term.children()
    variables = list(term.variables)
    variables.sort(lambda x,y: cmp(x.name, y.name))
    # -> a & b & c, a & b & ~c, b & c & a, b & c & ~a
    minterns = qm.step0_minterms(variables, term)
    print(minterns)
    assert 3 == len(minterns)
    assert a & b & c  == minterns[0]
    assert a & b & ~c == minterns[1]
    assert ~a & b & c == minterns[2]

