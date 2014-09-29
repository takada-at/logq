# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .. import qm

def test_Bool():
    a, b, c = qm.Bool.create('abc')
    r = a | b
    assert r.name == 'a | b'

    r = (a | b) & c
    assert r.expand().name == 'a & c | b & c'

    r = a & (b | c)
    assert r.expand().name == 'a & b | a & c'

    r = a & (a | c)
    assert r.expand().name == 'a'

    r = (a | b) & (a | c)
    #->a | a&c | b&a | b&c
    #->a | b&a | b&c
    #->a | b&c
    assert r.expand().name == 'a | b & c'

