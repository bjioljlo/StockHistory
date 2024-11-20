"""
全域的service
"""
from SqlService import SqlService
from ReadLoadSystem import ReadLoadSystem
from DrawFigur import DrawFigur
from MongoService import MongoService
MYSQL:SqlService = None
READLOAD:ReadLoadSystem = None
DRAWFIGUR:DrawFigur = None
MONGO:MongoService = None