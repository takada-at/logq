# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import os
__DIR__ = os.path.abspath(os.path.dirname(__file__))

import ply.yacc as yacc
from .lexer import tokens
tokens

DEBUG = 0

class ParserException(Exception):
    pass

def p_expr(p):
    """expr : expr OR term
            | expr AND term
            | term
    """
    if len(p)==4:
        if p[2]=='OR':
            p[0] = p[1] | p[3]
        elif p[2]=='AND':
            p[0] = p[1] & p[3]
    else:
        p[0] = p[1]

def p_term(p):
    """
    term : NOT term
         | boolean_primary
    """
    if len(p)==3:
        p[0] = ~p[2]
    else:
        p[0] = p[1]

def p_boolean_primary(p):
    """boolean_primary : COLUMN binop literal
                       | function_call
    """
    if len(p)==4:
        col = p[1]
        op = p[2]
        if op == '=':
            p[0] = (col == p[3])
        elif op == '!=':
            p[0] = (col != p[3])
        elif op == '<':
            p[0] = (col < p[3])
        elif op == '<=':
            p[0] = (col <= p[3])
        elif op == '>':
            p[0] = (col > p[3])
        elif op == '>=':
            p[0] = (col >= p[3])
    else:
        if p[1][0] == 'contain':
            p[0] = col[1][1].contain(col[1][2])
        elif p[1][0] == 'contain':
            p[0] = col[1][1].contain(col[1][2])

def p_binop(p):
    """binop : EQ
             | NE
             | GT
             | GE
             | LT
             | LE
    """
    p[0] = p[1]

def p_function_call(p):
    """function_call : ID '(' arglist ')'
    """
    p[0] = [p[1]] + p[3]

def p_arglist(p):
    """
    arglist : arg
            | arglist ',' arg
    """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[3]

def p_arg(p):
    """
    arg : literal
        | COLUMN
    """
    p[0] = p[1]

def p_literal(p):
    """literal : STRING
               | NUMBER
    """
    p[0] = p[1]

def p_error(p):
    raise ParserException(str(p))

start = str('expr')
parser = yacc.yacc(outputdir=__DIR__, debug=DEBUG, write_tables=False)

def parse(f):
    ret = parser.parse(f.read())
    parser.restart()
    return ret


