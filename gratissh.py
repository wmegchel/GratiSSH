###################################################
#
# Wout Megchelenbrink
# April 20, 2020
# Interactive Job scheduler v0.1 alpha
# License: todo
#
################ TODO #######################
# x tunnel does not work
# x fix icon size OSX
# x edit connection window is very small on OSX (small input fields) => should scale, no?
# x center text horizontally in the TableView



# -------------- LATER ---------------------
# - why is the main menu lost in OSX
# - connection save, edit, delete => trigger a refresh signal + slot
# - connection menu disappears after connection saving, editing or deletion => trigger a renew
# - an object with the all connection should be preserved (otherwise you cannot connect)
# - split "make menu" and "show tabs"
# - always show the active tabs => conn.isConnected()
# - update to R version 4.0 (Friday)
# - encrypt/decrypt passphrase
# - sync does not work properly
# - check if the SSH tunnel is open, and if so do not create another one
# - add a "clear log" button
# - add SLURM support and "no scheduler"
# - add debug info
# - start up Rserver in the right directory
# - write manual
# - get log data from the DB as well
# - fix the "loss of connection" after edit or save connection
# - add possibility for auto logon per connection
# - make tabs closable (i.e. close connection and jobs)
# - add a license
# - submit to github
# - write messages to a status bar or message bar
###################################################

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from connections import Connection
from form_connection import FormConnection
from job_view import JobView
import config
import sys
import os

# Enable high DPI scaling
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# Use high DPI icons
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MyMainWindow(QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()

    def setupUi(self, *args, **kwargs):

        # if "connections" in kwargs.keys():
        #     # if you add one; it needs to be added to all these guys
        #     self.connections = kwargs['connections']
        #     self.labels = kwargs['labels']
        #     self.tabs = kwargs['tabs']
        #     self.connectionMenu = kwargs['connectionMenu']
        #     self.actionConnect = kwargs['actionConnect']
        #     self.actionEditConnection = kwargs['editConnection']
        #     self.actionDeleteConnection = kwargs['actionDeleteConnection']



        self.set_icons()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.showMaximized() # config.MAIN_WINDOW_SIZE[0], config.MAIN_WINDOW_SIZE[1])

        # Add central widget
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # Add tabwidget (tabs are created dynamically per connection)
        self.tabWidget = QTabWidget()
        q = QGridLayout(self.centralwidget)
        q.addWidget(self.tabWidget)

        # self.tabWidget.setGeometry()
        # self.tabWidget.setGeometry(QRect(0, 50, 800, 600))

        # Add menu bar
        self.actionAddConnection = QAction(self)
        self.actionAddConnection.setIcon(self.icon_add)
        self.actionAddConnection.setText("Add connection")
        self.actionAddConnection.triggered.connect(self.addConnection)

        self.menubar = QMenuBar(self)
#        self.menubar.setGeometry(QRect(0, 0, config.MAIN_WINDOW_SIZE[0], 40))
        self.menuConnections = QMenu(self.menubar)
        self.menuConnections.setTitle("Connections")
        self.menuConnections.addAction(self.actionAddConnection)

        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setTitle("Help")

        self.actionAbout = QAction(self)
        self.actionAbout.setText("About")
        self.actionAbout.setIcon(self.icon_info)

        self.actionHowToUse = QAction(self)
        self.actionHowToUse.setText("How to use")
        self.actionHowToUse.setIcon(self.icon_help)

        self.menuHelp.addAction(self.actionHowToUse)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuConnections.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menubar.setNativeMenuBar(False)
        self.setMenuBar(self.menubar)

        # Add Status bar
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.buildMenu()



    def buildMenu(self):
        connections = Connection.getAll()
        nConnections = len(connections)

        self.tabs = [None] * nConnections
        self.labels = [None] * nConnections
        self.connections = [None] * nConnections
        self.connectionMenu = [None] * nConnections
        self.actionConnect = [None] * nConnections
        self.actionEditConnection = [None] * nConnections
        self.actionDeleteConnection = [None] * nConnections

        # Loop over the available connections
        for i in range(nConnections):

            self.connections[i] = Connection(connectionID=connections[i]['connectionID'])

            # Connection menu
            self.connectionMenu[i] = QMenu(self.menuConnections)
            self.connectionMenu[i].setIcon(self.icon_disconnected)
            self.connectionMenu[i].setTitle(self.connections[i].connectionName)

            # Connection submenu
            # connect
            self.actionConnect[i] = QAction(self)
            self.actionConnect[i].setText("Connect")
            self.actionConnect[i].setIcon(self.icon_connect)
            self.actionConnect[i].setObjectName("btnConnect_%d_%d" % (connections[i]["connectionID"], i))
            self.actionConnect[i].triggered.connect(self.connect)
            self.connectionMenu[i].addAction(self.actionConnect[i])

            # check
            # self.actionCheckConnection[i] = QAction(self)
            # self.actionCheckConnection[i].setText("Check status")
            # self.actionCheckConnection[i].setIcon(self.icon_check_connection)
            # self.actionCheckConnection[i].setObjectName("checkConnection_%d" % connections[i]["connectionID"])
            # self.actionCheckConnection[i].triggered.connect(self.checkConnection)
            # self.connectionMenu[i].addAction(self.actionCheckConnection[i])

            # edit
            self.actionEditConnection[i] = QAction(self)
            self.actionEditConnection[i].setText("Edit")
            self.actionEditConnection[i].setIcon(self.icon_edit)
            self.actionEditConnection[i].setObjectName("editConnection_%d" % connections[i]["connectionID"])
            self.actionEditConnection[i].triggered.connect(self.editConnection)
            self.connectionMenu[i].addAction(self.actionEditConnection[i])

            # delete
            self.actionDeleteConnection[i] = QAction(self)
            self.actionDeleteConnection[i].setText("Delete")
            self.actionDeleteConnection[i].setIcon(self.icon_delete)
            self.actionDeleteConnection[i].setObjectName("deleteConnection_%d" % connections[i]["connectionID"])
            self.actionDeleteConnection[i].triggered.connect(self.deleteConnection)

            self.connectionMenu[i].addAction(self.actionDeleteConnection[i])
            self.menuConnections.addAction(self.connectionMenu[i].menuAction())

            # Tab pages for active connections
            if self.connections[i].isConnected():
                jv = JobView(self.connections[i])
                self.tabWidget.addTab(jv, self.icon_disconnected, "blaataap")
                self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tabs[i]), self.icon_connected)
            else:
                self.connectionLabel = QLabel(self.tabs[i])
                self.connectionLabel.setGeometry(QRect(30, 50, 221, 34))
                self.connectionLabel.setText("Not connected to %s " % connections[i]['connectionName'])
                self.connectionLabel.adjustSize()

        self.tabWidget.setCurrentIndex(0)

    def connect(self):
        #print("dispatching to MAIN::CONNECT")

        tabID = int(self.sender().objectName().split(sep="_")[2])
        connectionID = int(self.sender().objectName().split(sep="_")[1])
        #print("dispatching to MAIN::CONNECT with tabID=%d and connectionID=%d" % (tabID, connectionID))
        conn = Connection(connectionID=connectionID)
        self.jv = JobView(connection=conn)
        conn.setJobView(self.jv)
        conn.connectToHost()  # whether this is a good place is unknown

        self.jv.showList()

        self.tabWidget.addTab(self.jv, self.icon_connected, conn.connectionName )
        self.jv.addButton.setEnabled(False)
        self.jv.deleteAllButton.setEnabled(False)
        self.jv.syncButton.setEnabled(False)

        #### 3. Change menu text to disconnect
        self.actionConnect[tabID].setText("Disconnect")


    def addConnection(self):
        frm = FormConnection(self)
        frm.setModal(True)
        frm.exec()
        #    self.setupUi()

           # msg = {'connectionID': 99999, 'jobID': None, 'message': "Connection '%s' created successfully" % frm.edtConnectionName.text(), 'messageType': 'SUCCESS'}
           # self.jv.writeLog(msg)

    def editConnection(self):
        connectionID = int(self.sender().objectName().split("_")[1])
        conn = Connection(connectionID=connectionID)
        frm = FormConnection(self, connection=conn)
        frm.setModal(True)
        frm.exec()
            # refresh
         #   self.setupUi()
            #msg = {'connectionID': connectionID, 'jobID': None, 'message': "Connection '%s' saved" % frm.edtConnectionName.text(), 'messageType': 'SUCCESS'}
            #self.jv.writeLog(msg)

    def deleteConnection(self):

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)

        conn = Connection(connectionID=int(self.sender().objectName().split("_")[1]))
        msg.setText("Delete connection %s?" % conn.connectionName)
        msg.setInformativeText("All jobs will be killed")
        msg.setWindowTitle("Delete connection")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if msg.exec() == QMessageBox.Ok:
            print("deleting all jobs")
            conn.deleteAllJobs()
            conn.delete()
            self.setupUi()
            #msg = {'connectionID': conn.connectionID, 'jobID': None, 'message': "Connection '%s' deleted" % conn.connectionName, 'messageType': 'SUCCESS'}
            #self.jv.writeLog(msg)

    def set_icons(self):


        # get the pyinstaller runtime directory
        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        # Icons main menu
        self.icon_add = QIcon()
        self.icon_add.addPixmap(QPixmap(os.path.join(basedir, "add_connection_normal_32px.png")), QIcon.Normal, QIcon.Off)
        self.icon_connected = QIcon()
        self.icon_connected.addPixmap(QPixmap(os.path.join(basedir, "network_connected_32px.png")), QIcon.Normal, QIcon.Off)
        self.icon_disconnected = QIcon()
        self.icon_disconnected.addPixmap(QPixmap(os.path.join(basedir, "network_disconnected_32px.png")), QIcon.Normal, QIcon.Off)
        self.icon_info = QIcon()
        self.icon_info.addPixmap(QPixmap(os.path.join(basedir, "info_32px.png")), QIcon.Normal, QIcon.Off)
        self.icon_help = QIcon()
        self.icon_help.addPixmap(QPixmap(os.path.join(basedir, "help_32px.png")), QIcon.Normal, QIcon.Off)

        # Icons submenu
        self.icon_connect = QIcon()
        self.icon_connect.addPixmap(QPixmap(os.path.join(basedir, "network_connected_32px.png")), QIcon.Normal, QIcon.Off)
      #  self.icon_check_connection = QIcon()
      #  self.icon_check_connection.addPixmap(QPixmap("icons/network_check-24px.svg"), QIcon.Normal,
       #                                      QIcon.Off)
        self.icon_edit = QIcon()
        self.icon_edit.addPixmap(QPixmap(os.path.join(basedir, "edit_connection_normal_32px.png")), QIcon.Normal, QIcon.Off)
        self.icon_delete = QIcon()
        self.icon_delete.addPixmap(QPixmap(os.path.join(basedir, "delete_connection_normal_32px.png")), QIcon.Normal, QIcon.Off)


if __name__ == "__main__":


    from PyQt5 import QtGui

    # Clear logs
    config.DB.table("Log").purge()
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet("QGroupBox { font-weight: bold; } ")
    ui = MyMainWindow()
    ui.setupUi()
    ui.show()
    sys.exit(app.exec_())
