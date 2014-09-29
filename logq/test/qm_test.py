# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import qm

def test_Bool():
    a, b, c, d = qm.Bool.create('abcd')
    r = a | b
    assert r.name == 'a | b'

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
    assert r.normalize().name == 'a | b & c'

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

