import os
from PyQt5 import QtGui, QtCore
#from connection import Connection
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from sshconf import read_ssh_config


class ConnectionForm(QDialog):

    def __init__(self, connection):
        super(QDialog, self).__init__()

        self.connection = connection
        if self.connection.connectionName is not "" and self.connection.connectionName is not None:
            self.setWindowTitle("Edit connection %s" % self.connection.connectionName)
        else:
            self.setWindowTitle("New connection")

        self.showForm()



    def showForm(self):

        err = False

        self.resize(1050, 400)
        vLayout = QVBoxLayout(self)

        font = QFont()
        font.setBold(True)
        font.setWeight(75)

        # Message box
        self.msgBox = QFrame(self)
        self.msgBox.setFixedWidth(850)
        self.msgBox.setFixedHeight(40)
        self.msgTxt = QLabel(self.msgBox)
        self.msgTxt.setFont(font)
        self.msgTxt.setStyleSheet("color: white")

        vLayout.addWidget(self.msgBox)
        self.groupboxConnection = QGroupBox("Connection settings")
        vLayout.addWidget(self.groupboxConnection)

        frmLayout = QFormLayout(self.groupboxConnection)

        # Host combobox
        self.cmbHost = QComboBox()
        self.cmbHost.clear()
        self.cmbHost.addItems(self.getHostNames("~/.ssh/config"))

        index = self.cmbHost.findText(self.connection.hostName, Qt.MatchFixedString)
        if index >= 0:
            self.cmbHost.setCurrentIndex(index)

        # Connection name
        self.edtConnectionName = QLineEdit(self.connection.connectionName)
        # self.edtConnectionName.setText()

        self.edtPassphrase = QLineEdit(self.connection.passphrase)
        # self.edtPassphrase.setText()
        self.edtPassphrase.setEchoMode(QLineEdit.Password)

        # Grid engine radio group
        self.radioSLURM = QRadioButton("SLURM")
        self.radioSGE = QRadioButton("SGE")
        self.radioNone = QRadioButton("None")

        if self.connection.gridEngine == "SLURM":
            self.radioSLURM.setChecked(True)
        elif self.connection.gridEngine == "SGE":
            self.radioSGE.setChecked(True)
        else:
            self.radioNone.setChecked(True)

        gridEngineHBox = QHBoxLayout()
        gridEngineHBox.addWidget(self.radioSLURM)
        gridEngineHBox.addWidget(self.radioSGE)
        gridEngineHBox.addWidget(self.radioNone)

        # Singularity folder
        self.edtSingularityFolder = QLineEdit(self.connection.singularityFolder)
        # self.edtSingularityFolder.setText(

        # Project folder
        self.edtProjectRootFolder = QLineEdit(self.connection.projectRootFolder)
        # self.edtProjectRootFolder.setText()

        # Add all to the form
        frmLayout.addRow(QLabel("Host name:"), self.cmbHost)
        frmLayout.addRow(QLabel("Connection name:"), self.edtConnectionName)
        frmLayout.addRow(QLabel("Passphrase:"), self.edtPassphrase)
        frmLayout.addRow(QLabel("Grid engine:"),  gridEngineHBox)
        frmLayout.addRow(QLabel("Singularity folder:"), self.edtSingularityFolder)
        frmLayout.addRow(QLabel("Project root folder:"), self.edtProjectRootFolder)

        QBtn = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.validate)
        self.buttonBox.rejected.connect(self.reject)

        vLayout.addWidget(self.buttonBox)



    def validate(self):
        if self.edtConnectionName.text() == "":
            self.showMsg("Please enter the connection name", "err")
            return False
        elif self.edtSingularityFolder.text() == "":
            self.showMsg("Please enter the remote singularity folder name", "err")
            return False
        elif self.edtProjectRootFolder.text() == "":
            self.showMsg("Please enter the remote project root folder name", "err")
            return False

        config = read_ssh_config(os.path.expanduser("~/.ssh/config"))
        settings = config.host(self.cmbHost.currentText())

        keys = {k.lower(): v for k, v in settings.items()}
        if "user" not in keys:
            self.showMsg("SSH config file does not provide user for host %s" % self.cmbHost.currentText(), "err")
            return False

        if "proxycommand" not in keys:
            self.showMsg("SSH config file does not provide ProxyCommand for host %s" % self.cmbHost.currentText(), "err")
            return False

        self.accept()

        return True

    # move to connection
    # def save(self, frm):
    #     if frm.radioNone.isChecked():
    #         gridEngine = "None"
    #     elif frm.radioSGE.isChecked():
    #         gridEngine = "SGE"
    #     else:
    #         gridEngine = "SLURM"
    #
    #     # save the connection
    #     self.hostName=frm.cmbHost.currentText()
    #     self.connectionName=frm.edtConnectionName.text()
    #     self.passphrase=frm.edtPassphrase.text()
    #     self.gridEngine=gridEngine
    #     self.projectRootFolder=frm.edtProjectRootFolder.text()
    #     self.singularityFolder=frm.edtSingularityFolder.text()
    #
    #     if self.connectionID:
    #         self.tblConnections.update({'hostName': self.hostName,
    #                                     'connectionName': self.connectionName,
    #                                     'passphrase': self.passphrase,
    #                                     'gridEngine': self.gridEngine,
    #                                     'projectRootFolder': self.projectRootFolder,
    #                                     'singularityFolder': self.singularityFolder},
    #                                    where('connectionID') == self.connectionID)
    #     else:
    #         connectionID = self.tblConnections.insert({'hostName': self.hostName,
    #                                                    'connectionName': self.connectionName,
    #                                                    'passphrase': self.passphrase,
    #                                                    'gridEngine': self.gridEngine,
    #                                                    'projectRootFolder': self.projectRootFolder,
    #                                                    'singularityFolder': self.singularityFolder})
    #
    #         # Sort of mysql_insert_id
    #         self.tblConnections.update({'connectionID': connectionID}, doc_ids=[connectionID])
    #         self.connectionID = connectionID
    #     return self




    def showMsg(self, msgText, msgType):
        if msgType == "err":
            self.msgBox.setStyleSheet("background-color:red")
            self.msgTxt.setText(msgText)
            self.msgTxt.adjustSize()



    def getHostNames(self, filename):
        filename = os.path.expanduser(filename)
        try:
            conf = read_ssh_config(filename)
            h = list(conf.hosts())
            if "*" in h:
                h.remove("*")
            h.sort()
            return h

        except FileNotFoundError as e:
            print("File not found: ", e)





