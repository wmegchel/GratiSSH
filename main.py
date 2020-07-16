###################################################
#
# Wout Megchelenbrink
# April 20, 2020
# Interactive Job scheduler v0.1 alpha
# License: todo
#

# - fixed disconnect


################ TODO #######################
# x tunnel does not work
# x fix icon size OSX
# x edit connection window is very small on OSX (small input fields) => should scale, no?
# x center text horizontally in the TableView







# -------------- LATER ---------------------
# - why is the main menu lost in OSX ??
# x connection save, edit, delete => trigger a refresh signal + slot
# x connection menu disappears after connection saving, editing or deletion => trigger a renew
# x an object with the all connection should be preserved (otherwise you cannot connect) (DONE)
# x split "make menu" and "show tabs" (DONE)
# x always show the active tabs => conn.isConnected() (DONE)
# x update to latest Rstudio
# x update to R version 4.0 (Friday)
# x encrypt/decrypt passphrase => probably not possible
# x sync does not work properly
# x check if the SSH tunnel is open, and if so do not create another one
# x add a "clear log" button
# x add SLURM support
# x add no schedulure support
# - add debug info
# x start up Rserver in the right directory
# - write manual
# - get log data from the DB as well
# x fix the "loss of connection" after edit or save connection (DONE)
# - add possibility for auto logon per connection
# - make tabs closable (i.e. close connection and jobs)
# - add a license
# - submit to github
# x write messages to a status bar or message bar (DONE)
###################################################

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from connection import Connection
from connection_form import ConnectionForm
from joblist import JobList
import config, sys, os
from about import About
import webbrowser

# Enable high DPI scaling
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# Use high DPI icons
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MyMainWindow(QMainWindow):

    def __init__(self):
        super(MyMainWindow, self).__init__()

        # Get the available connections from the DB
        self.menuConnection = {}
        self.subItemConnect = {}
        self.subItemEdit = {}
        self.subItemDelete = {}
        self.jobList = {}
        self.connections = Connection.getAll()

    def setupUi(self, *args, **kwargs):
        self.set_icons()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.showMaximized() # config.MAIN_WINDOW_SIZE[0], config.MAIN_WINDOW_SIZE[1])

        # Central widget
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # Add tab widget (tabs are created dynamically per connection)
        self.tabWidget = QTabWidget()
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.addWidget(self.tabWidget)

        # show menu and tabs
        self.showMenu()
        self.showTabs()


    def showMenu(self):

        # menu bar
        self.menubar = QMenuBar(self)

        # connection menu
        self.menuConnections = QMenu(self.menubar)
        self.menuConnections.setTitle("Connections")

        # connection -> add_connection
        self.actionAddConnection = QAction(self)
        self.actionAddConnection.setIcon(self.icon_add)
        self.actionAddConnection.setText("Add connection")
        self.actionAddConnection.triggered.connect(self.addConnection)
        self.menuConnections.addAction(self.actionAddConnection)

        # Add all existing connections to the menu
        for connectionID, conn in self.connections.items():
            self.addConnectionToMenu(conn)

        # help menu
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setTitle("Help")

        # help -> about
        self.actionAbout = QAction(self)
        self.actionAbout.setText("About")
        self.actionAbout.setIcon(self.icon_info)
        self.actionAbout.triggered.connect(self.about)

        # help -> how_to_use
        self.actionHowToUse = QAction(self)
        self.actionHowToUse.setText("How to use")
        self.actionHowToUse.setIcon(self.icon_help)
        self.actionHowToUse.triggered.connect(self.help)

        self.menuHelp.addAction(self.actionHowToUse)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuConnections.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menubar.setNativeMenuBar(False)
        self.setMenuBar(self.menubar)

        # Add status bar
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

    def addConnectionToMenu(self, conn):

        # Connection menu
        self.menuConnection[conn.connectionID] = QMenu(self.menuConnections)
        self.menuConnection[conn.connectionID].setIcon(self.icon_disconnected)
        self.menuConnection[conn.connectionID].setTitle(conn.connectionName)

        # Connection -> "server_name" => connect
        self.subItemConnect[conn.connectionID] = QAction(self)
        self.subItemConnect[conn.connectionID].setText("Connect")
        self.subItemConnect[conn.connectionID].setIcon(self.icon_connect)
        # self.subItemConnect[conn.connectionID].setObjectName("btnConnect_%d" % conn.connectionID)
        self.subItemConnect[conn.connectionID].triggered.connect(lambda: self.connect(conn.connectionID))
        self.menuConnection[conn.connectionID].addAction(self.subItemConnect[conn.connectionID])

        # Connection -> "server_name" => edit
        self.subItemEdit[conn.connectionID] = QAction(self)
        self.subItemEdit[conn.connectionID].setText("Edit")
        self.subItemEdit[conn.connectionID].setIcon(self.icon_edit)
        # self.subItemEdit[conn.connectionID].setObjectName("editConnection_%d" % conn.connectionID)
        self.subItemEdit[conn.connectionID].triggered.connect(lambda: self.editConnection(conn.connectionID))
        self.menuConnection[conn.connectionID].addAction(self.subItemEdit[conn.connectionID])

        # Connection -> "server_name" => delete
        self.subItemDelete[conn.connectionID] = QAction(self)
        self.subItemDelete[conn.connectionID].setText("Delete")
        self.subItemDelete[conn.connectionID].setIcon(self.icon_delete)
        # self.subItemDelete[conn.connectionID].setObjectName("deleteConnection_%d" % conn.connectionID)
        self.subItemDelete[conn.connectionID].triggered.connect(lambda: self.deleteConnection(conn.connectionID))
        self.menuConnection[conn.connectionID].addAction(self.subItemDelete[conn.connectionID])

        # Append menuItem
        self.menuConnections.addAction(self.menuConnection[conn.connectionID].menuAction())

    # also here, better to loop over the connections themselves
    def showTabs(self):
        #print("showing tab pages now")
        i = 1
        for connectionID, conn in self.connections.items():
            #print("init tabview for connection %d" % connectionID)

            # instantiate a JT model, with the connectionand a view
            #self.connections[connectionID].jobTableModel = JobTableModel(conn)
            self.jobList[connectionID] = JobList(conn)
            # model = JobTableModel(conn)
            # self.jobTableViews[connectionID] = JobTableView(model)

            # Tab pages for active connections
            self.tabWidget.addTab(self.jobList[connectionID], self.icon_disconnected, conn.connectionName)

            if conn.isConnected():
                self.tabWidget.setTabIcon(i, self.icon_connected)
            else:
                self.tabWidget.setTabIcon(i, self.icon_disconnected)

            i+=1
            #self.tabWidget.setTabsClosable(True)


    def connect(self, connectionID):

        if self.subItemConnect[connectionID].text() == "Connect":
            conn = self.connections[connectionID]
            self.jobList[connectionID].syncJobs()

            # update icons to connected
            self.menuConnection[conn.connectionID].setIcon(self.icon_connected)

            index = self.tabWidget.indexOf(self.jobList[connectionID])
            self.tabWidget.setCurrentIndex(index)
            self.tabWidget.setTabIcon(index, self.icon_connected)

            # change menu text to disconnect
            self.subItemConnect[connectionID].setText("Disconnect")

            self.jobList[connectionID].isConnected()

        else:
            msg = {'connectionID': connectionID,
                   "jobID": None,
                    "message": "Connection closed",
                    "messageType": "SUCCESS"}
            self.jobList[connectionID].writeLog(msg)
            self.connections[connectionID].disconnect()
            index = self.tabWidget.indexOf(self.jobList[connectionID])
            self.tabWidget.setCurrentIndex(index)
            self.tabWidget.setTabIcon(index, self.icon_disconnected)
            self.subItemConnect[connectionID].setText("Connect")
            self.jobList[connectionID].isDisconnected()


    def addConnection(self):

        frm = ConnectionForm(Connection())
        frm.setModal(True)
        if frm.exec():
            if frm.radioNone.isChecked():
                gridEngine = "None"
            elif frm.radioSGE.isChecked():
                gridEngine = "SGE"
            else:
                gridEngine = "SLURM"

            # save the connection
            conn = Connection(connectionID=None,
                              connectionName=frm.edtConnectionName.text(),
                              hostName=frm.cmbHost.currentText(),
                              passphrase=frm.edtPassphrase.text(),
                              gridEngine=gridEngine,
                              projectRootFolder=frm.edtProjectRootFolder.text(),
                              singularityFolder=frm.edtSingularityFolder.text())
            connNew = conn.save()
            connectionID = connNew.connectionID

            message = "Connection %s successfully created" % connNew.connectionName
            icon = self.icon_disconnected

            msg = {'connectionID': connNew.connectionID,
                   'jobID': None,
                   'message': message,
                   'messageType': 'SUCCESS'}

            self.jobList[connectionID] = JobList(connNew)
            self.jobList[connectionID].writeLog(msg)

            # Update the menu and the tab
            self.addConnectionToMenu(connNew)
            #self.menuConnection[connectionID].setTitle(connNew.connectionName)

            # Replace tab
            self.tabWidget.addTab(self.jobList[connectionID], icon, connNew.connectionName)
            index = self.tabWidget.indexOf(self.jobList[connectionID])
            self.tabWidget.setCurrentIndex(index)

            # Replace or add connection
            self.connections[connectionID] = connNew


    def editConnection(self, connectionID):
        frm = ConnectionForm(self.connections[connectionID])
        frm.setModal(True)
        if frm.exec():
            if frm.radioNone.isChecked():
                gridEngine = "None"
            elif frm.radioSGE.isChecked():
                gridEngine = "SGE"
            else:
                gridEngine = "SLURM"

            # save the connection
            conn = Connection(connectionID=connectionID,
                              connectionName=frm.edtConnectionName.text(),
                              hostName=frm.cmbHost.currentText(),
                              passphrase=frm.edtPassphrase.text(),
                              gridEngine=gridEngine,
                              projectRootFolder=frm.edtProjectRootFolder.text(),
                              singularityFolder=frm.edtSingularityFolder.text(),
                              threadpool=self.connections[connectionID].threadpool,
                              sshClient=self.connections[connectionID].sshClient,
                              sftpClient=self.connections[connectionID].sftpClient)
            connUpdated = conn.save()

            if self.connections[connectionID].isConnected():
                message = "Connection settings updated. Reconnecting and syncing jobs..."
                icon = self.icon_connected
            else:
                message = "Connection settings updated."
                icon = self.icon_disconnected

            msg = {'connectionID': connUpdated.connectionID,
                   'jobID': None,
                   'message': message,
                   'messageType': 'SUCCESS'}

            self.jobList[connectionID].updateConnection(connUpdated)
            self.jobList[connectionID].writeLog(msg)

            # Reconnect, if we were connected
            if self.connections[connectionID].isConnected():
                self.jobList[connectionID].syncJobs()

            # Update the menu and the tab
            self.menuConnection[connectionID].setTitle(connUpdated.connectionName)

            # Replace tab
            index = self.tabWidget.indexOf(self.jobList[connectionID])
            self.tabWidget.removeTab(index)
            self.tabWidget.insertTab(index, self.jobList[connectionID], icon, connUpdated.connectionName)
            self.tabWidget.setCurrentIndex(index)

            # Replace or add connection
            self.connections[connectionID] = connUpdated



    def deleteConnection(self, connectionID):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)

        # connectionID = int(self.sender().objectName().split("_")[1])
        conn = self.connections[connectionID]
        #print("deleting connection %d and %d", (connectionID, conn.connectionID))

        msg.setText("Delete connection %s?" % conn.connectionName)
        msg.setInformativeText("All jobs will be killed")
        msg.setWindowTitle("Delete connection")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if msg.exec() == QMessageBox.Ok:
            #print("deleting all jobs")
            # delete all jobs
            self.jobList[connectionID].deleteAllJobs()

            # remove the connection from the DB
            conn.delete()

            # remove connection the tab
            index = self.tabWidget.indexOf(self.jobList[connectionID])
            self.tabWidget.removeTab(index)

            # Remove the connection from the menu
            self.menuConnections.removeAction(self.menuConnection[connectionID].menuAction())

            # remove the submenu items
            del self.menuConnection[connectionID]

            # remove the connection jobList
            del self.jobList[connectionID]

            # remove the connection object
            del self.connections[connectionID]


    def about(self):
        about = About()
        about.setModal(True)
        about.exec()

    def help(self):
        webbrowser.open_new_tab("https://github.com/wmegchel/GratiSSH/")


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
    # Clear logs
#    config.DB.table("Log").purge()
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet("QGroupBox { font-weight: bold; } ")
    ui = MyMainWindow()
    ui.setupUi()
    ui.show()
    sys.exit(app.exec_())
