# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from . import engine
from . import enginefactory as ef

class LogFile(object):
    def __init__(self, fileobject):
        if isinstance(fileobject, str) or isinstance(fileobject, unicode):
            fileobject = open(fileobject)

        self.fileobject = fileobject

    def search(self, query):
        ef.EngineFactory.set_engineclass(engine.Engine)
        eng = ef.compile_query(query)
        colmap = {str(k): v for k, v in query.columns()}
        self.fileobject.seek(0)
        return self.parser(eng, self.fileobject, colmap)


class CSVFile(LogFile):
    parser = engine.CSVParser


