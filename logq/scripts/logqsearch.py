# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
from logq.queryparser import parser
from logq import logfile

def logf(ftype):
    d = {
        'csv': logfile.CSVFile,
        'ltsv': logfile.LTSVFile,
        }
    return d[ftype]

def expr(string):
    try:
        exprobj = parser.parses(string)
    except:
        raise Exception('syntax error: {}'.format(string))

    return exprobj

def search(path, expr, fileformat):
    ftype = logf(fileformat)
    logobj = ftype(open(path))
    for row in logobj.search(expr):
        print(row)

def main():
    parser = argparse.ArgumentParser(description='Search Log File.')
    parser.add_argument('-f', '--format', choices=('csv', 'ltsv'), default='csv')
    parser.add_argument('-s', '--sep', default=',')
    parser.add_argument('-q', '--quote', default='"')
    parser.add_argument('path')
    parser.add_argument('expr', type=expr)
    args = parser.parse_args()
    search(args.path, args.expr, args.format)

if __name__=='__main__':
    main()

