# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from . import engine
from . import enginefactory as ef

class LogFile(object):
    def __init__(self, fileobject, **params):
        if isinstance(fileobject, str) or isinstance(fileobject, unicode):
            fileobject = open(fileobject)

        self.fileobject = fileobject
        self._params = params

    def _create_parser(self, engine, colmap, fileobject):
        return self.parser(engine, fileobject, colmap)

    def _colmap(self, query):
        return {str(k): v for k, v in query.columns()}

    def search(self, query):
        ef.EngineFactory.set_engineclass(engine.Engine)
        eng = ef.compile_query(query)
        colmap = self._colmap(query)
        return self._create_parser(eng, colmap, self.fileobject)

class CSVFile(LogFile):
    parser = engine.CSVParser
    def _colmap(self, query):
        return query.col_list()

    def _create_parser(self, engine, colmap, fileobject):
        delimiter = bytes(self._params.get('delimiter', ','))
        quotechar = bytes(self._params.get('delimiter', '"'))
        return self.parser(engine, fileobject, colmap, delimiter=delimiter, quotechar=quotechar)

class LTSVFile(LogFile):
    parser = engine.LTSVParser

