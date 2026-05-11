import os
import sys

from PyQt5 import QtWidgets

# 確保無論從哪個路徑執行，都能正確匯入 src.* 套件
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.Common.CacheService import HybridCacheService
from src.Common.ConfigService import load_config, get_config_path
from src.Common.ConcurrentUtils import ConcurrentUtils
from src.Controller.MediatorController import Mediator_Controller, controllers
from src.DrawFigur import DrawFigur
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockReportHistory import SeasonReportFactory, MonthReportFactory, DayReportFactory, DividendYieldReportFactory, ADLReportFactory
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.ScheduleService import ScheduleService
from src.SqlService import SqlService
from src.UpdateStockService.StockDataDownloader import StockDataDownloader
from src.UpdateStockService.StockDataSynchronizer import StockDataSynchronizer
from src.UpdateStockService.ADLUpdater import ADLUpdater

app = QtWidgets.QApplication(sys.argv)
config = load_config(get_config_path())

# 1. Initialize all services
sql_service = SqlService()
sql_service.RunMysql()
mongo_service = MongoService()
mongo_service.RunMongoDB(config.get('database.mongodb'))
draw_figur_service = DrawFigur()
concurrent_utils = ConcurrentUtils()
read_load_system = ReadLoadSystem(sqlservice=sql_service)

# Initialize hybrid cache service (Redis L1 + MongoDB L2)
cache_service = HybridCacheService(
    mongo_service=mongo_service,
    sql_service=sql_service,
    config_path=get_config_path(),
    cache_size=100  # 快取 100 支熱門股票
)

external_data_factory = ExternalDataFactory(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system,
    cache_service=cache_service  # 注入快取服務
)
# 初始化所有 Report Factory - Mediator 預期是已經建立好的 Report 實例
from src.Common.InfomationType import FS_type

# 正確作法：先建立 Report 實例，因為 MediatorController 設計是直接使用實例而非工廠函數
season_report_factory = SeasonReportFactory(FS_type.BS, external_data_factory)
month_report_factory = MonthReportFactory(external_data_factory)
day_report_factory = DayReportFactory(external_data_factory)
dividend_yield_report_factory = DividendYieldReportFactory(external_data_factory)
adl_report_factory = ADLReportFactory(external_data_factory)

# Initialize Update Stock components (no facade)
retry_attempts = config.get('external_apis.yahoo_finance.retry_attempts', 3)
stock_data_downloader = StockDataDownloader(retry_attempts, 1.0)
stock_data_synchronizer = StockDataSynchronizer(sql_service, mongo_service)
adl_updater = ADLUpdater(sql_service, external_data_factory)

schedule_service = ScheduleService(
    concurrent_utils=concurrent_utils,
    stock_data_downloader=stock_data_downloader,
    stock_data_synchronizer=stock_data_synchronizer,
    adl_updater=adl_updater,
    external_data_factory=external_data_factory,
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system,
    config=config,
    cache_service=cache_service
)

# 2. Inject all services into the Mediator_Controller
mediator_controller = Mediator_Controller(
    schedule=schedule_service,
    sql_service=sql_service,
    mongo_service=mongo_service,
    draw_figur_service=draw_figur_service,
    concurrent_utils=concurrent_utils,
    season_report_factory=season_report_factory,
    month_report_factory=month_report_factory,
    day_report_factory=day_report_factory,
    dividend_yield_report_factory=dividend_yield_report_factory,
    adl_report_factory=adl_report_factory,
    external_data_factory=external_data_factory
)

mediator_controller.GetController(controllers.Main).ShowWindow()

sys.exit(app.exec_())
