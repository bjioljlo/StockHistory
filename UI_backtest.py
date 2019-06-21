# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_backtest.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow3(object):
    def setupUi(self, MainWindow3):
        MainWindow3.setObjectName("MainWindow3")
        MainWindow3.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow3)
        self.centralwidget.setObjectName("centralwidget")
        self.date_start = QtWidgets.QDateEdit(self.centralwidget)
        self.date_start.setGeometry(QtCore.QRect(60, 40, 110, 24))
        self.date_start.setObjectName("date_start")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(80, 20, 60, 16))
        self.label.setObjectName("label")
        self.date_end = QtWidgets.QDateEdit(self.centralwidget)
        self.date_end.setGeometry(QtCore.QRect(200, 40, 110, 24))
        self.date_end.setObjectName("date_end")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(220, 20, 60, 16))
        self.label_2.setObjectName("label_2")
        self.button_backtest = QtWidgets.QPushButton(self.centralwidget)
        self.button_backtest.setGeometry(QtCore.QRect(460, 420, 113, 32))
        self.button_backtest.setObjectName("button_backtest")
        MainWindow3.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow3)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow3.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow3)
        self.statusbar.setObjectName("statusbar")
        MainWindow3.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow3)
        QtCore.QMetaObject.connectSlotsByName(MainWindow3)

    def retranslateUi(self, MainWindow3):
        _translate = QtCore.QCoreApplication.translate
        MainWindow3.setWindowTitle(_translate("MainWindow3", "回測"))
        self.label.setText(_translate("MainWindow3", "開始日期"))
        self.label_2.setText(_translate("MainWindow3", "結束日期"))
        self.button_backtest.setText(_translate("MainWindow3", "開始回測"))


