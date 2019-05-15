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
        MainWindow2.resize(520, 668)
        self.centralwidget = QtWidgets.QWidget(MainWindow2)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 10, 91, 21))
        self.label.setObjectName("label")
        self.input_GPM = QtWidgets.QTextEdit(self.centralwidget)
        self.input_GPM.setGeometry(QtCore.QRect(140, 10, 81, 21))
        self.input_GPM.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.input_GPM.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.input_GPM.setObjectName("input_GPM")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 121, 21))
        self.label_2.setObjectName("label_2")
        self.input_OPR = QtWidgets.QTextEdit(self.centralwidget)
        self.input_OPR.setGeometry(QtCore.QRect(140, 40, 81, 21))
        self.input_OPR.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.input_OPR.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.input_OPR.setObjectName("input_OPR")
        self.button_pick = QtWidgets.QPushButton(self.centralwidget)
        self.button_pick.setGeometry(QtCore.QRect(460, 560, 113, 32))
        self.button_pick.setObjectName("button_pick")
        self.treeView_pick = QtWidgets.QTreeView(self.centralwidget)
        self.treeView_pick.setGeometry(QtCore.QRect(20, 70, 511, 171))
        self.treeView_pick.setObjectName("treeView_pick")
        self.button_moveToInput = QtWidgets.QPushButton(self.centralwidget)
        self.button_moveToInput.setGeometry(QtCore.QRect(30, 260, 113, 32))
        self.button_moveToInput.setObjectName("button_moveToInput")
        MainWindow2.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow2)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 520, 22))
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
        self.label.setText(_translate("MainWindow2", "毛利率(%)大於"))
        self.label_2.setText(_translate("MainWindow2", "營業利益率(%)大於"))
        self.button_pick.setText(_translate("MainWindow2", "開始篩選"))
        self.button_moveToInput.setText(_translate("MainWindow2", "帶入"))


