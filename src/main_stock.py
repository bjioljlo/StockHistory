import os
import sys

from PyQt5 import QtWidgets

# 確保無論從哪個路徑執行，都能正確匯入 src.* 套件
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.Common.ConfigService import load_config, get_config_path
from src.Common.ConcurrentUtils import ConcurrentUtils
from src.Common.DataCleanupService import DataCleanupService
from src.Controller.MediatorController import Mediator_Controller, controllers
from src.DrawFigur import DrawFigur
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.GetStockData import ReportServices
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.ScheduleService import ScheduleService
from src.SqlService import SqlService
from src.UpdateStockService import UpdateStockService

app = QtWidgets.QApplication(sys.argv)
config = load_config(get_config_path())

# 1. Initialize all services
sql_service = SqlService()
sql_service.RunMysql()
mongo_service = MongoService()
mongo_service.RunMongoDB(config['database']['mongodb'])
draw_figur_service = DrawFigur()
concurrent_utils = ConcurrentUtils()
read_load_system = ReadLoadSystem(sqlservice=sql_service)

external_data_factory = ExternalDataFactory(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system
)
report_services = ReportServices(external_data_factory=external_data_factory)

updateStock_service = UpdateStockService(sql_service=sql_service, mongo_service=mongo_service, read_load_system=read_load_system, config=config)
schedule_service = ScheduleService(concurrent_utils=concurrent_utils, update_stockService=updateStock_service)

# 2. Inject all services into the Mediator_Controller
mediator_controller = Mediator_Controller(
    schedule=schedule_service,
    sql_service=sql_service,
    mongo_service=mongo_service,
    draw_figur_service=draw_figur_service,
    concurrent_utils=concurrent_utils,
    report_services=report_services,
    external_data_factory=external_data_factory
)

mediator_controller.GetController(controllers.Main).ShowWindow()

sys.exit(app.exec_())
