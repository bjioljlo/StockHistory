import sys

from PyQt5 import QtWidgets

from Common import Globals
from Common import ConfigService
from Controller.MediatorController import Mediator_Controller, controllers
from DrawFigur import DrawFigur
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from ScheduleService import ScheduleService
from SqlService import SqlService
from ThreadPool import ThreadPool

app = QtWidgets.QApplication(sys.argv)
config = ConfigService.load_config()
Globals.MYSQL = SqlService()
Globals.MYSQL.RunMysql()
Globals.DRAWFIGUR = DrawFigur()
Globals.MONGO = MongoService()
Globals.MONGO.RunMongoDB(config['database']['mongodb'])
Globals.THREADPOOL = ThreadPool()
Globals.READLOAD = ReadLoadSystem()
Schedule = ScheduleService()
mediator_controller = Mediator_Controller(Schedule)
mediator_controller.ShowWindow(controllers.Main)

sys.exit(app.exec_())
