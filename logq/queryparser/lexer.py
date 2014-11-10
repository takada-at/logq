# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import ply.lex as lex

DEBUG = 0
tokens = (
    'OR', 'AND', 'NOT',
    'BIN_OP', 'COLUMN', 'ID',
    'NUMBER',
    'STRING',
)
literals = [ '(',')', ',']

t_OR = r'OR'
t_AND = r'AND'
t_NOT = r'NOT'

def t_BIN_OP(t):
    r'=|!=|>=|>|<=|<|<>'
    return t

def t_COLUMN(t):
    r'\$[a-zA-Z0-9\-_]+'
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9\-_]*'
    return t

def t_STRING(t):
    r'\"(?P<content>([^\\\n]|(\\.))*?)\"'
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

lexer = lex.lex(debug=DEBUG)

