from PyQt5 import QtWidgets
import sys
import telegram_bot

import update_stock_info

from View.View_main import Main_Window, MyWindow
from View.View_pick import Pick_Window, MyPickWindow
from View.View_backtest import BackTest_Window, MyBacktestWindow

from Model.Model_main import Model_main
from Model.Model_pick import Model_pick
from Model.Model_backtest import Model_backtest

from Controller.Controller_main import Controller_main
from Controller.Controller_pick import Controller_pick
from Controller.Controller_backTest import Controller_backTest

main_titalList = ["股票號碼","股票名稱"]
pick_titalList = ["股票號碼","股票名稱","每股參考淨值","基本每股盈餘（元）",
                "毛利率(%)","營業利益率(%)","資產總額","負債總額","股本",
                "權益總額","本期綜合損益總額（稅後）","PBR","PER","PEG","ROE","殖利率"]

app = QtWidgets.QApplication(sys.argv)
controller_backtest = Controller_backTest(BackTest_Window(MyBacktestWindow()), Model_backtest())
controller_pick = Controller_pick(Pick_Window(MyPickWindow()), Model_pick(controller_backtest))
controller_main = Controller_main(Main_Window(MyWindow()), Model_main(controller_pick))

controller_main.View.GetFormUI().show()

update_stock_info.RunMysql()
try:
    sys.exit(app.exec_())
except:#退出時需要清理的方法
    print('開始清理異步內存')
    telegram_bot.stop_telegram(telegram_bot.updater)
    update_stock_info.stopThreadSchedule()