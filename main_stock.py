import sys

from PyQt5 import QtWidgets

import Globals
from Controller import Mediator_Controller, controllers, mediator_controller
from DrawFigur import DrawFigur
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from ScheduleService import ScheduleService
from SqlService import SqlService

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
except Exception:  # 退出時需要清理的方法
    print("開始清理異步內存")
    Schedule.StopThreadSchedule()
