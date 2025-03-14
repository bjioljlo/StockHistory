"""
全域的service
"""

from DrawFigur import DrawFigur
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from SqlService import SqlService
from ThreadPool import ThreadPool

MYSQL: SqlService = None
READLOAD: ReadLoadSystem = None
DRAWFIGUR: DrawFigur = None
MONGO: MongoService = None
THREADPOOL: ThreadPool = None
