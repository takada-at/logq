# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import os
__DIR__ = os.path.abspath(os.path.dirname(__file__))

import ply.yacc as yacc

from lexer import tokens
tokens
DEBUG = 0

def p_expr(p):
    """expr : expr OR expr
            | expr AND expr
            | NOT expr
            | boolean_primary
    """
    pass

def p_boolean_primary(p):
    """boolean_primary: COLUMN BIN_OP literal
                      | function_call
    """
    pass

def p_function_call(p):
    """function_call: ID '(' arglist ')'
    """
    pass

def p_arglist(p):
    """
    arglist : arg
            | arglist ',' arg
    """
    pass

def p_arg(p):
    """
    arg: literal
       | COLUMN
    """

def p_literal(p):
    """literal: STRING
              | NUMBER
    """
    pass

start = str('po_file')
parser = yacc.yacc(outputdir=__DIR__, debug=DEBUG, write_tables=False)

def parse(f):
    ret = parser.parse(f.read())
    parser.restart()
    return ret


