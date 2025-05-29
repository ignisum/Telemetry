# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'telemetry_client.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QHeaderView, QLabel,
    QLayout, QListWidget, QListWidgetItem, QMainWindow,
    QPushButton, QSizePolicy, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from custom_table import PacketTable

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(868, 764)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setBaseSize(QSize(0, 0))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(9, 9, 851, 731))
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_4 = QVBoxLayout(self.tab_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, -1)
        self.btnConnect = QPushButton(self.tab_3)
        self.btnConnect.setObjectName(u"btnConnect")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btnConnect.sizePolicy().hasHeightForWidth())
        self.btnConnect.setSizePolicy(sizePolicy2)
        self.btnConnect.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.verticalLayout.addWidget(self.btnConnect)

        self.btnStart = QPushButton(self.tab_3)
        self.btnStart.setObjectName(u"btnStart")
        sizePolicy2.setHeightForWidth(self.btnStart.sizePolicy().hasHeightForWidth())
        self.btnStart.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.btnStart)

        self.btnStop = QPushButton(self.tab_3)
        self.btnStop.setObjectName(u"btnStop")
        sizePolicy2.setHeightForWidth(self.btnStop.sizePolicy().hasHeightForWidth())
        self.btnStop.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.btnStop)


        self.verticalLayout_4.addLayout(self.verticalLayout)

        self.PacketTableWidget = PacketTable(self.tab_3)
        self.PacketTableWidget.setObjectName(u"PacketTableWidget")
        self.PacketTableWidget.setEnabled(True)

        self.verticalLayout_4.addWidget(self.PacketTableWidget)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        sizePolicy.setHeightForWidth(self.tab_4.sizePolicy().hasHeightForWidth())
        self.tab_4.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(self.tab_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.btnRefreshSessions = QPushButton(self.tab_4)
        self.btnRefreshSessions.setObjectName(u"btnRefreshSessions")

        self.verticalLayout_5.addWidget(self.btnRefreshSessions)

        self.lblSessionInfo = QLabel(self.tab_4)
        self.lblSessionInfo.setObjectName(u"lblSessionInfo")

        self.verticalLayout_5.addWidget(self.lblSessionInfo)

        self.listSessions = QListWidget(self.tab_4)
        self.listSessions.setObjectName(u"listSessions")
        sizePolicy.setHeightForWidth(self.listSessions.sizePolicy().hasHeightForWidth())
        self.listSessions.setSizePolicy(sizePolicy)

        self.verticalLayout_5.addWidget(self.listSessions)

        self.tableSessionPackets = QTableWidget(self.tab_4)
        self.tableSessionPackets.setObjectName(u"tableSessionPackets")
        sizePolicy.setHeightForWidth(self.tableSessionPackets.sizePolicy().hasHeightForWidth())
        self.tableSessionPackets.setSizePolicy(sizePolicy)
        self.tableSessionPackets.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.tableSessionPackets.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.verticalLayout_5.addWidget(self.tableSessionPackets)

        self.tabWidget.addTab(self.tab_4, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.btnConnect.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f \u043a \u0441\u0435\u0440\u0432\u0435\u0440\u0443", None))
#if QT_CONFIG(tooltip)
        self.btnStart.setToolTip(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043f\u0443\u0441\u043a\u0430\u0435\u0442 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044e \u0438 \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0443 \u0442\u0435\u043b\u0435\u043c\u0435\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0434\u0430\u043d\u043d\u044b\u0445", None))
#endif // QT_CONFIG(tooltip)
        self.btnStart.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0447\u0430\u0442\u044c \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0443 \u0434\u0430\u043d\u043d\u044b\u0445", None))
#if QT_CONFIG(tooltip)
        self.btnStop.setToolTip(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0435\u0442 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044e \u0434\u0430\u043d\u043d\u044b\u0445", None))
#endif // QT_CONFIG(tooltip)
        self.btnStop.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0443 \u0434\u0430\u043d\u043d\u044b\u0445", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0436\u0438\u043c \u0440\u0435\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u0440\u0435\u043c\u0435\u043d\u0438", None))
        self.btnRefreshSessions.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0435\u0441\u0441\u0438\u0438", None))
        self.lblSessionInfo.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0441\u0441\u0438\u044e \u0434\u043b\u044f \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0430", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u0441\u0435\u0441\u0441\u0438\u0439", None))
    # retranslateUi

