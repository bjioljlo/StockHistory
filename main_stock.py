from PyQt5 import QtWidgets
import sys
import Globals
from ScheduleService import ScheduleService
from SqlService import SqlService
from ReadLoadSystem import ReadLoadSystem
from MongoService import MongoService
from Controller import mediator_controller, Mediator_Controller, controllers
from DrawFigur import DrawFigur

app = QtWidgets.QApplication(sys.argv)
Globals.MYSQL = SqlService()
Globals.MYSQL.RunMysql()
Globals.DRAWFIGUR = DrawFigur()
Globals.MONGO = MongoService()
Globals.MONGO.RunMongoDB()

Globals.READLOAD = ReadLoadSystem()
Schedule = ScheduleService(Globals.MYSQL, Globals.READLOAD)
mediator_controller = Mediator_Controller(Schedule)
mediator_controller.ShowWindow(controllers.Main)

try:
    sys.exit(app.exec_())
except: #退出時需要清理的方法
    print('開始清理異步內存')
    Schedule.StopThreadSchedule()