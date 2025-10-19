import sys

from PyQt5 import QtWidgets

from Common import ConfigService
from Controller.MediatorController import Mediator_Controller, controllers
from DrawFigur import DrawFigur
from ExternalService.ExternalDataFactory import ExternalDataFactory
from FilterService.GetStockData import ReportServices
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from ScheduleService import ScheduleService
from SqlService import SqlService
from ThreadPool import ThreadPool
from UpdateStockService import UpdateStockService

app = QtWidgets.QApplication(sys.argv)
config = ConfigService.load_config()

# 1. Initialize all services
sql_service = SqlService()
sql_service.RunMysql()
mongo_service = MongoService()
mongo_service.RunMongoDB(config['database']['mongodb'])
draw_figur_service = DrawFigur()
thread_pool_service = ThreadPool()
read_load_system = ReadLoadSystem(sqlservice=sql_service)

external_data_factory = ExternalDataFactory(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system
)
report_services = ReportServices(external_data_factory=external_data_factory)

updateStock_service = UpdateStockService(sql_service=sql_service, mongo_service=mongo_service, read_load_system=read_load_system)
schedule_service = ScheduleService(thread_pool=thread_pool_service, update_stockService=updateStock_service)

# 2. Inject all services into the Mediator_Controller
mediator_controller = Mediator_Controller(
    schedule=schedule_service,
    sql_service=sql_service,
    mongo_service=mongo_service,
    draw_figur_service=draw_figur_service,
    thread_pool=thread_pool_service,
    report_services=report_services,
    external_data_factory=external_data_factory
)

mediator_controller.GetController(controllers.Main).ShowWindow()

sys.exit(app.exec_())
