# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import ply.lex as lex
from ..expr import Column

DEBUG = 0
tokens = [
    'COLUMN', 'ID',
    'EQ', 'NE', 'GT', 'GE', 'LT', 'LE',
    'NUMBER',
    'STRING',
]
reserved = {
    'OR': 'OR',
    'AND': 'AND',
    'NOT': 'NOT',
}
tokens += reserved.keys()
literals = [ '(',')', ',']

t_EQ = '='
t_NE = '!='
t_GT = '>'
t_GE = '>='
t_LT = '<'
t_LE = '<='
t_OR = r'OR'
t_AND = r'AND'
t_NOT = r'NOT'


def t_COLUMN(t):
    r'\$(?P<col>[a-zA-Z0-9\-_]+)'
    stval = t.lexer.lexmatch.group('col')
    if stval is None: stval = ''
    t.value = Column(stval)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9\-_]*'
    t.type = reserved.get(t.value.upper(),'ID')
    if t.type!='ID':
        t.value = t.value.upper()
    return t

def t_STRING(t):
    '(\'|\\")(?P<content>([^\\\\\\n]|(\\\\.))*?)(\\"|\')'
    stval = t.lexer.lexmatch.group("content")
    t.value = stval if stval else ''
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore  = ' \t'

def t_error(t):
    raise SyntaxError("Illegal character %r on %d" % (t.value[0], t.lexer.lineno))

lexer = lex.lex(debug=DEBUG, reflags=re.IGNORECASE)

