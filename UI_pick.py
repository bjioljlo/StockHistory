# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_pick.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow2(object):
    def setupUi(self, MainWindow2):
        MainWindow2.setObjectName("MainWindow2")
        MainWindow2.resize(700, 670)
        self.centralwidget = QtWidgets.QWidget(MainWindow2)
        self.centralwidget.setObjectName("centralwidget")
        self.treeView_pick = QtWidgets.QTreeView(self.centralwidget)
        self.treeView_pick.setGeometry(QtCore.QRect(10, 380, 671, 211))
        self.treeView_pick.setObjectName("treeView_pick")
        self.button_moveToInput = QtWidgets.QPushButton(self.centralwidget)
        self.button_moveToInput.setGeometry(QtCore.QRect(570, 590, 113, 32))
        self.button_moveToInput.setObjectName("button_moveToInput")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(10, 10, 251, 191))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 249, 189))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.Ana_ProfitAndLoss = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.Ana_ProfitAndLoss.setGeometry(QtCore.QRect(10, 0, 111, 31))
        self.Ana_ProfitAndLoss.setObjectName("Ana_ProfitAndLoss")
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setGeometry(QtCore.QRect(30, 30, 91, 21))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_2.setGeometry(QtCore.QRect(30, 60, 121, 21))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_3.setGeometry(QtCore.QRect(40, 110, 81, 21))
        self.label_3.setObjectName("label_3")
        self.Ana_BalanceSheet = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.Ana_BalanceSheet.setGeometry(QtCore.QRect(10, 80, 111, 31))
        self.Ana_BalanceSheet.setObjectName("Ana_BalanceSheet")
        self.Ana_CPAndLoss = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.Ana_CPAndLoss.setGeometry(QtCore.QRect(10, 130, 111, 31))
        self.Ana_CPAndLoss.setObjectName("Ana_CPAndLoss")
        self.label_4 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_4.setGeometry(QtCore.QRect(20, 160, 101, 21))
        self.label_4.setObjectName("label_4")
        self.button_pick = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_pick.setGeometry(QtCore.QRect(140, 0, 113, 32))
        self.button_pick.setObjectName("button_pick")
        self.input_EPS = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.input_EPS.setGeometry(QtCore.QRect(130, 160, 71, 24))
        self.input_EPS.setMaximum(999.99)
        self.input_EPS.setObjectName("input_EPS")
        self.input_RPS = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.input_RPS.setGeometry(QtCore.QRect(120, 110, 71, 24))
        self.input_RPS.setMaximum(999.99)
        self.input_RPS.setObjectName("input_RPS")
        self.input_OPR = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.input_OPR.setGeometry(QtCore.QRect(150, 60, 71, 24))
        self.input_OPR.setMaximum(999.99)
        self.input_OPR.setObjectName("input_OPR")
        self.input_GPM = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.input_GPM.setGeometry(QtCore.QRect(130, 30, 71, 24))
        self.input_GPM.setMaximum(999.99)
        self.input_GPM.setObjectName("input_GPM")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea_2 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_2.setGeometry(QtCore.QRect(10, 200, 251, 171))
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 249, 169))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.label_5 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_5.setGeometry(QtCore.QRect(20, 30, 121, 21))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_6.setGeometry(QtCore.QRect(20, 50, 121, 21))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_7.setGeometry(QtCore.QRect(-10, 0, 101, 31))
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.label_28 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_28.setGeometry(QtCore.QRect(10, 70, 181, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.button_pick_2 = QtWidgets.QPushButton(self.scrollAreaWidgetContents_2)
        self.button_pick_2.setGeometry(QtCore.QRect(120, 0, 113, 32))
        self.button_pick_2.setObjectName("button_pick_2")
        self.input_OMGR = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_OMGR.setGeometry(QtCore.QRect(200, 70, 48, 24))
        self.input_OMGR.setMaximum(999)
        self.input_OMGR.setObjectName("input_OMGR")
        self.input_monthRP_UpMpnth = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_monthRP_UpMpnth.setGeometry(QtCore.QRect(140, 50, 48, 24))
        self.input_monthRP_UpMpnth.setMaximum(99)
        self.input_monthRP_UpMpnth.setObjectName("input_monthRP_UpMpnth")
        self.input_monthRP_smoothAVG = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_monthRP_smoothAVG.setGeometry(QtCore.QRect(140, 30, 48, 24))
        self.input_monthRP_smoothAVG.setMaximum(99)
        self.input_monthRP_smoothAVG.setObjectName("input_monthRP_smoothAVG")
        self.label_32 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_32.setGeometry(QtCore.QRect(10, 90, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_32.setFont(font)
        self.label_32.setObjectName("label_32")
        self.input_FCF = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_FCF.setGeometry(QtCore.QRect(150, 90, 48, 24))
        self.input_FCF.setMaximum(999)
        self.input_FCF.setObjectName("input_FCF")
        self.label_33 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_33.setGeometry(QtCore.QRect(10, 110, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_33.setFont(font)
        self.label_33.setObjectName("label_33")
        self.input_ROE = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_ROE.setGeometry(QtCore.QRect(150, 110, 48, 24))
        self.input_ROE.setMaximum(999)
        self.input_ROE.setObjectName("input_ROE")
        self.label_34 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.label_34.setGeometry(QtCore.QRect(10, 130, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_34.setFont(font)
        self.label_34.setObjectName("label_34")
        self.input_EPS_up = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_2)
        self.input_EPS_up.setGeometry(QtCore.QRect(150, 130, 48, 24))
        self.input_EPS_up.setMaximum(999)
        self.input_EPS_up.setObjectName("input_EPS_up")
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.button_openBackWindow = QtWidgets.QPushButton(self.centralwidget)
        self.button_openBackWindow.setGeometry(QtCore.QRect(460, 590, 113, 32))
        self.button_openBackWindow.setObjectName("button_openBackWindow")
        self.scrollArea_3 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_3.setGeometry(QtCore.QRect(260, 280, 211, 91))
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollArea_3.setObjectName("scrollArea_3")
        self.scrollAreaWidgetContents_3 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_3.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_3.setObjectName("scrollAreaWidgetContents_3")
        self.label_8 = QtWidgets.QLabel(self.scrollAreaWidgetContents_3)
        self.label_8.setGeometry(QtCore.QRect(20, 50, 101, 21))
        self.label_8.setObjectName("label_8")
        self.label_10 = QtWidgets.QLabel(self.scrollAreaWidgetContents_3)
        self.label_10.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setObjectName("label_10")
        self.check_volum_Max = QtWidgets.QCheckBox(self.scrollAreaWidgetContents_3)
        self.check_volum_Max.setGeometry(QtCore.QRect(30, 30, 87, 20))
        self.check_volum_Max.setObjectName("check_volum_Max")
        self.input_volum = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_3)
        self.input_volum.setGeometry(QtCore.QRect(100, 50, 71, 24))
        self.input_volum.setMaximum(9999)
        self.input_volum.setObjectName("input_volum")
        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_3)
        self.scrollArea_4 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_4.setGeometry(QtCore.QRect(260, 10, 211, 91))
        self.scrollArea_4.setWidgetResizable(True)
        self.scrollArea_4.setObjectName("scrollArea_4")
        self.scrollAreaWidgetContents_4 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_4.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_4.setObjectName("scrollAreaWidgetContents_4")
        self.label_9 = QtWidgets.QLabel(self.scrollAreaWidgetContents_4)
        self.label_9.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_9.setObjectName("label_9")
        self.label_11 = QtWidgets.QLabel(self.scrollAreaWidgetContents_4)
        self.label_11.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(self.scrollAreaWidgetContents_4)
        self.label_12.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_12.setObjectName("label_12")
        self.input_price_high = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_4)
        self.input_price_high.setGeometry(QtCore.QRect(90, 30, 81, 24))
        self.input_price_high.setMaximum(9999)
        self.input_price_high.setObjectName("input_price_high")
        self.input_price_low = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_4)
        self.input_price_low.setGeometry(QtCore.QRect(90, 60, 81, 24))
        self.input_price_low.setMaximum(9999)
        self.input_price_low.setObjectName("input_price_low")
        self.scrollArea_4.setWidget(self.scrollAreaWidgetContents_4)
        self.scrollArea_5 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_5.setGeometry(QtCore.QRect(260, 100, 211, 91))
        self.scrollArea_5.setWidgetResizable(True)
        self.scrollArea_5.setObjectName("scrollArea_5")
        self.scrollAreaWidgetContents_5 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_5.setObjectName("scrollAreaWidgetContents_5")
        self.label_13 = QtWidgets.QLabel(self.scrollAreaWidgetContents_5)
        self.label_13.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(self.scrollAreaWidgetContents_5)
        self.label_14.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_14.setAlignment(QtCore.Qt.AlignCenter)
        self.label_14.setObjectName("label_14")
        self.label_15 = QtWidgets.QLabel(self.scrollAreaWidgetContents_5)
        self.label_15.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_15.setObjectName("label_15")
        self.input_PBR_high = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_5)
        self.input_PBR_high.setGeometry(QtCore.QRect(70, 30, 71, 24))
        self.input_PBR_high.setMaximum(999.99)
        self.input_PBR_high.setObjectName("input_PBR_high")
        self.input_PBR_low = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_5)
        self.input_PBR_low.setGeometry(QtCore.QRect(70, 60, 71, 24))
        self.input_PBR_low.setMaximum(999.99)
        self.input_PBR_low.setObjectName("input_PBR_low")
        self.scrollArea_5.setWidget(self.scrollAreaWidgetContents_5)
        self.scrollArea_6 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_6.setGeometry(QtCore.QRect(260, 190, 211, 91))
        self.scrollArea_6.setWidgetResizable(True)
        self.scrollArea_6.setObjectName("scrollArea_6")
        self.scrollAreaWidgetContents_6 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_6.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_6.setObjectName("scrollAreaWidgetContents_6")
        self.label_16 = QtWidgets.QLabel(self.scrollAreaWidgetContents_6)
        self.label_16.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_16.setObjectName("label_16")
        self.label_17 = QtWidgets.QLabel(self.scrollAreaWidgetContents_6)
        self.label_17.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_17.setAlignment(QtCore.Qt.AlignCenter)
        self.label_17.setObjectName("label_17")
        self.label_18 = QtWidgets.QLabel(self.scrollAreaWidgetContents_6)
        self.label_18.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_18.setObjectName("label_18")
        self.input_PER_high = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_6)
        self.input_PER_high.setGeometry(QtCore.QRect(90, 30, 71, 24))
        self.input_PER_high.setMaximum(999.99)
        self.input_PER_high.setObjectName("input_PER_high")
        self.input_PER_low = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_6)
        self.input_PER_low.setGeometry(QtCore.QRect(90, 60, 71, 24))
        self.input_PER_low.setMaximum(999.99)
        self.input_PER_low.setObjectName("input_PER_low")
        self.scrollArea_6.setWidget(self.scrollAreaWidgetContents_6)
        self.scrollArea_7 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_7.setGeometry(QtCore.QRect(470, 190, 211, 91))
        self.scrollArea_7.setWidgetResizable(True)
        self.scrollArea_7.setObjectName("scrollArea_7")
        self.scrollAreaWidgetContents_7 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_7.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_7.setObjectName("scrollAreaWidgetContents_7")
        self.label_19 = QtWidgets.QLabel(self.scrollAreaWidgetContents_7)
        self.label_19.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_19.setObjectName("label_19")
        self.label_20 = QtWidgets.QLabel(self.scrollAreaWidgetContents_7)
        self.label_20.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_20.setAlignment(QtCore.Qt.AlignCenter)
        self.label_20.setObjectName("label_20")
        self.label_21 = QtWidgets.QLabel(self.scrollAreaWidgetContents_7)
        self.label_21.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_21.setObjectName("label_21")
        self.input_ROE_low = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_7)
        self.input_ROE_low.setGeometry(QtCore.QRect(70, 60, 71, 24))
        self.input_ROE_low.setMaximum(999.99)
        self.input_ROE_low.setObjectName("input_ROE_low")
        self.input_ROE_high = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_7)
        self.input_ROE_high.setGeometry(QtCore.QRect(70, 30, 71, 24))
        self.input_ROE_high.setMaximum(999.99)
        self.input_ROE_high.setObjectName("input_ROE_high")
        self.scrollArea_7.setWidget(self.scrollAreaWidgetContents_7)
        self.scrollArea_8 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_8.setGeometry(QtCore.QRect(470, 10, 211, 91))
        self.scrollArea_8.setWidgetResizable(True)
        self.scrollArea_8.setObjectName("scrollArea_8")
        self.scrollAreaWidgetContents_8 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_8.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_8.setObjectName("scrollAreaWidgetContents_8")
        self.label_22 = QtWidgets.QLabel(self.scrollAreaWidgetContents_8)
        self.label_22.setGeometry(QtCore.QRect(0, 30, 101, 21))
        self.label_22.setObjectName("label_22")
        self.label_23 = QtWidgets.QLabel(self.scrollAreaWidgetContents_8)
        self.label_23.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_23.setAlignment(QtCore.Qt.AlignCenter)
        self.label_23.setObjectName("label_23")
        self.label_24 = QtWidgets.QLabel(self.scrollAreaWidgetContents_8)
        self.label_24.setGeometry(QtCore.QRect(0, 60, 101, 21))
        self.label_24.setObjectName("label_24")
        self.input_yiled_high = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_8)
        self.input_yiled_high.setGeometry(QtCore.QRect(90, 30, 71, 24))
        self.input_yiled_high.setMaximum(999.99)
        self.input_yiled_high.setObjectName("input_yiled_high")
        self.input_yiled_low = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_8)
        self.input_yiled_low.setGeometry(QtCore.QRect(90, 60, 71, 24))
        self.input_yiled_low.setMaximum(999.99)
        self.input_yiled_low.setObjectName("input_yiled_low")
        self.scrollArea_8.setWidget(self.scrollAreaWidgetContents_8)
        self.scrollArea_9 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_9.setGeometry(QtCore.QRect(470, 100, 211, 91))
        self.scrollArea_9.setWidgetResizable(True)
        self.scrollArea_9.setObjectName("scrollArea_9")
        self.scrollAreaWidgetContents_9 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_9.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_9.setObjectName("scrollAreaWidgetContents_9")
        self.label_25 = QtWidgets.QLabel(self.scrollAreaWidgetContents_9)
        self.label_25.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_25.setObjectName("label_25")
        self.label_26 = QtWidgets.QLabel(self.scrollAreaWidgetContents_9)
        self.label_26.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_26.setAlignment(QtCore.Qt.AlignCenter)
        self.label_26.setObjectName("label_26")
        self.label_27 = QtWidgets.QLabel(self.scrollAreaWidgetContents_9)
        self.label_27.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_27.setObjectName("label_27")
        self.input_flash_Day = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_9)
        self.input_flash_Day.setGeometry(QtCore.QRect(60, 30, 48, 24))
        self.input_flash_Day.setMaximum(99)
        self.input_flash_Day.setObjectName("input_flash_Day")
        self.input_record_Day = QtWidgets.QSpinBox(self.scrollAreaWidgetContents_9)
        self.input_record_Day.setGeometry(QtCore.QRect(80, 60, 48, 24))
        self.input_record_Day.setMaximum(99)
        self.input_record_Day.setObjectName("input_record_Day")
        self.scrollArea_9.setWidget(self.scrollAreaWidgetContents_9)
        self.scrollArea_10 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_10.setGeometry(QtCore.QRect(470, 280, 211, 91))
        self.scrollArea_10.setWidgetResizable(True)
        self.scrollArea_10.setObjectName("scrollArea_10")
        self.scrollAreaWidgetContents_10 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_10.setGeometry(QtCore.QRect(0, 0, 209, 89))
        self.scrollAreaWidgetContents_10.setObjectName("scrollAreaWidgetContents_10")
        self.label_29 = QtWidgets.QLabel(self.scrollAreaWidgetContents_10)
        self.label_29.setGeometry(QtCore.QRect(10, 30, 101, 21))
        self.label_29.setObjectName("label_29")
        self.label_30 = QtWidgets.QLabel(self.scrollAreaWidgetContents_10)
        self.label_30.setGeometry(QtCore.QRect(60, 0, 101, 31))
        self.label_30.setAlignment(QtCore.Qt.AlignCenter)
        self.label_30.setObjectName("label_30")
        self.label_31 = QtWidgets.QLabel(self.scrollAreaWidgetContents_10)
        self.label_31.setGeometry(QtCore.QRect(10, 60, 101, 21))
        self.label_31.setObjectName("label_31")
        self.input_PEG_high = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_10)
        self.input_PEG_high.setGeometry(QtCore.QRect(90, 30, 71, 24))
        self.input_PEG_high.setMaximum(999.99)
        self.input_PEG_high.setObjectName("input_PEG_high")
        self.input_PEG_low = QtWidgets.QDoubleSpinBox(self.scrollAreaWidgetContents_10)
        self.input_PEG_low.setGeometry(QtCore.QRect(90, 60, 71, 24))
        self.input_PEG_low.setMaximum(999.99)
        self.input_PEG_low.setObjectName("input_PEG_low")
        self.scrollArea_10.setWidget(self.scrollAreaWidgetContents_10)
        self.button_inputNum = QtWidgets.QPushButton(self.centralwidget)
        self.button_inputNum.setGeometry(QtCore.QRect(10, 590, 113, 32))
        self.button_inputNum.setObjectName("button_inputNum")
        MainWindow2.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow2)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 700, 22))
        self.menubar.setObjectName("menubar")
        MainWindow2.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow2)
        self.statusbar.setObjectName("statusbar")
        MainWindow2.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow2)
        QtCore.QMetaObject.connectSlotsByName(MainWindow2)

    def retranslateUi(self, MainWindow2):
        _translate = QtCore.QCoreApplication.translate
        MainWindow2.setWindowTitle(_translate("MainWindow2", "財報挑選"))
        self.button_moveToInput.setText(_translate("MainWindow2", "帶入"))
        self.Ana_ProfitAndLoss.setText(_translate("MainWindow2", "營益分析彙總表"))
        self.label.setText(_translate("MainWindow2", "毛利率(%)大於"))
        self.label_2.setText(_translate("MainWindow2", "營業利益率(%)大於"))
        self.label_3.setText(_translate("MainWindow2", "每股參考淨值"))
        self.Ana_BalanceSheet.setText(_translate("MainWindow2", "資產負債彙總表"))
        self.Ana_CPAndLoss.setText(_translate("MainWindow2", "綜合損益彙總表"))
        self.label_4.setText(_translate("MainWindow2", "基本每股盈餘(元)"))
        self.button_pick.setText(_translate("MainWindow2", "開始篩選"))
        self.label_5.setText(_translate("MainWindow2", "月營收往前平滑月份"))
        self.label_6.setText(_translate("MainWindow2", "月營收連續升高月份"))
        self.label_7.setText(_translate("MainWindow2", "逐步升高篩選"))
        self.label_28.setText(_translate("MainWindow2", "同季營業利益成長率連續增高季數"))
        self.button_pick_2.setText(_translate("MainWindow2", "開始篩選"))
        self.label_32.setText(_translate("MainWindow2", "自由現金流連續增高季數"))
        self.label_33.setText(_translate("MainWindow2", "ROE連續增高季數"))
        self.label_34.setText(_translate("MainWindow2", "EPS連續增高季數"))
        self.button_openBackWindow.setText(_translate("MainWindow2", "開啟回測視窗"))
        self.label_8.setText(_translate("MainWindow2", "交易量(萬元)"))
        self.label_10.setText(_translate("MainWindow2", "交易量篩選"))
        self.check_volum_Max.setText(_translate("MainWindow2", "取最大交易量"))
        self.label_9.setText(_translate("MainWindow2", "股價範圍(高)"))
        self.label_11.setText(_translate("MainWindow2", "股價範圍篩選"))
        self.label_12.setText(_translate("MainWindow2", "股價範圍(低)"))
        self.label_13.setText(_translate("MainWindow2", "PBR(高)"))
        self.label_14.setText(_translate("MainWindow2", "股價淨值比篩選"))
        self.label_15.setText(_translate("MainWindow2", "PBR(低)"))
        self.label_16.setText(_translate("MainWindow2", "PER(高)"))
        self.label_17.setText(_translate("MainWindow2", "本益比篩選"))
        self.label_18.setText(_translate("MainWindow2", "PER(低)"))
        self.label_19.setText(_translate("MainWindow2", "ROE(高)"))
        self.label_20.setText(_translate("MainWindow2", "股東權益報酬率"))
        self.label_21.setText(_translate("MainWindow2", "ROE(低)"))
        self.label_22.setText(_translate("MainWindow2", "殖利率範圍(高)"))
        self.label_23.setText(_translate("MainWindow2", "殖利率範圍篩選"))
        self.label_24.setText(_translate("MainWindow2", "殖利率範圍(低)"))
        self.label_25.setText(_translate("MainWindow2", "幾天內"))
        self.label_26.setText(_translate("MainWindow2", "創新高篩選"))
        self.label_27.setText(_translate("MainWindow2", "創新高天數"))
        self.label_29.setText(_translate("MainWindow2", "PEG(高)"))
        self.label_30.setText(_translate("MainWindow2", "本益成長比篩選"))
        self.label_31.setText(_translate("MainWindow2", "PEG(低)"))
        self.button_inputNum.setText(_translate("MainWindow2", "帶入價值數值"))


