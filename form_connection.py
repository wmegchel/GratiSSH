import os
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QLabel, QLineEdit, \
        QGroupBox, QDialog, QComboBox, QHBoxLayout, QRadioButton, QFrame, QDialogButtonBox
from sshconf import read_ssh_config
from PyQt5 import QtGui, QtCore
from connections import Connection


class FormConnection(QDialog):

    def __init__(self, *args, **kwargs):
        super(QDialog, self).__init__(*args)

        if "connection" in kwargs.keys():
            self.connection = kwargs['connection']
            self.setWindowTitle("Edit connection %s" % self.connection.connectionName)
        else:
            self.connection = Connection()
            self.setWindowTitle("Add new connection")

        self.showForm()


    def showForm(self):

        self.resize(1150, 400)

        self.vLayout = QVBoxLayout(self)

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)

        # Message box
        self.msgBox = QFrame(self)
        self.msgBox.setFixedWidth(850)
        self.msgBox.setFixedHeight(40)
        self.msgTxt = QLabel(self.msgBox)
        self.msgTxt.setFont(font)
        self.msgTxt.setStyleSheet("color: white")

        self.vLayout.addWidget(self.msgBox)
        self.groupboxConnection = QGroupBox("Connection settings")
        self.vLayout.addWidget(self.groupboxConnection)

        self.frmLayout = QFormLayout(self.groupboxConnection)

        # Host combobox
        self.cmbHost = QComboBox()
        self.cmbHost.clear()
        self.cmbHost.addItems(self.__getHostNames("~/.ssh/config"))

        index = self.cmbHost.findText(self.connection.hostName, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cmbHost.setCurrentIndex(index)

        # Connection name
        self.edtConnectionName = QLineEdit()
        self.edtConnectionName.setText(self.connection.connectionName)

        self.edtPassphrase = QLineEdit()
        self.edtPassphrase.setText(self.connection.passphrase)
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

        self.gridEngineHBox = QHBoxLayout()
        self.gridEngineHBox.addWidget(self.radioSLURM)
        self.gridEngineHBox.addWidget(self.radioSGE)
        self.gridEngineHBox.addWidget(self.radioNone)

        # Singularity folder
        self.edtSingularityFolder = QLineEdit()
        self.edtSingularityFolder.setText(self.connection.singularityFolder)

        # Project folder
        self.edtProjectRootFolder = QLineEdit()
        self.edtProjectRootFolder.setText(self.connection.projectRootFolder)

        # Add all to the form
        self.frmLayout.addRow(QLabel("Host name:"), self.cmbHost)
        self.frmLayout.addRow(QLabel("Connection name:"), self.edtConnectionName)
        self.frmLayout.addRow(QLabel("Passphrase:"), self.edtPassphrase)
        self.frmLayout.addRow(QLabel("Grid engine:"),  self.gridEngineHBox)
        self.frmLayout.addRow(QLabel("Singularity folder:"), self.edtSingularityFolder)
        self.frmLayout.addRow(QLabel("Project root folder:"), self.edtProjectRootFolder)

        QBtn = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.save)
        self.buttonBox.rejected.connect(self.reject)

        self.vLayout.addWidget(self.buttonBox)


    def save(self):
        if self.validate():
            if self.radioNone.isChecked():
                gridEngine = "None"
            elif self.radioSGE.isChecked():
                gridEngine = "SGE"
            else:
                gridEngine = "SLURM"

            # save the connection
            conn = Connection(connectionID=self.connection.connectionID,
                              hostName=self.cmbHost.currentText(),
                              connectionName=self.edtConnectionName.text(),
                              passphrase=self.edtPassphrase.text(),
                              gridEngine=gridEngine,
                              projectRootFolder=self.edtProjectRootFolder.text(),
                              singularityFolder=self.edtSingularityFolder.text(),
                              update=True)
            conn.save()

            # close the form
            self.accept()

            # rebuild the menu
            self.parent().setupUi()




    def validate(self):
        if self.edtConnectionName.text() == "":
            self.__showMessage("Please enter the connection name", "err")
            return False
        elif self.edtSingularityFolder.text() == "":
            self.__showMessage("Please enter the remote singularity folder name", "err")
            return False
        elif self.edtProjectRootFolder.text() == "":
            self.__showMessage("Please enter the remote project root folder name", "err")
            return False

        config = read_ssh_config(os.path.expanduser("~/.ssh/config"))
        settings = config.host(self.cmbHost.currentText())

        keys = {k.lower(): v for k, v in settings.items()}
        if "user" not in keys:
            self.__showMessage("SSH config file does not provide user for host %s" % self.cmbHost.currentText(), "err")
            return False

        if "proxycommand" not in keys:
            self.__showMessage("SSH config file does not provide ProxyCommand for host %s" % self.cmbHost.currentText(), "err")
            return False

        return True


    def __showMessage(self, msgText, msgType):
        if msgType == "err":
            self.msgBox.setStyleSheet("background-color:red")
            self.msgTxt.setText(msgText)
            self.msgTxt.adjustSize()



    def __getHostNames(self, filename):
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


