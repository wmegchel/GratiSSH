from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from job_model import Job
from datetime import datetime
from connections import Connection, ProgressDelegate
import config
from waitingspinnerwidget import QtWaitingSpinner
import webbrowser
from logger import Logger
import sys
import os


class JobView(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.connection = kwargs['connection']

        self.dbTable = config.DB.table("jobs")
        self.log = Logger(jobView=self)
        self.jobTable = QtWidgets.QTableView()
        self.tunnels = {}

        if "update" in kwargs.keys():
            # Set fields
            self.jobID = kwargs['jobID']
            self.jobName = kwargs['jobName']
            self.projectFolder = kwargs['projectFolder']
            self.runTime = kwargs['runTime']
            self.nCPU = kwargs['nCPU']
            self.nGPU = kwargs['nGPU']
            self.memory = kwargs['memory']
            self.singularityImg = kwargs['singularityImg']
        else:
            self.jobID = None
            self.jobName = ""
            self.projectFolder = None
            self.runTime = 2
            self.nCPU = 1
            self.nGPU = 0
            self.memory = 8
            self.singularityImg = None
            self.editor = "Jupyter Lab"

    def add(self):
        self.frm = self.showForm()
        self.frm.setModal(True)
        self.frm.exec()

    def save(self):
        if self.__validateForm(self.frm):

            # Check if the cookies folder exists; if not make it
            if not self.connection.file_exists("%s/%s/cookies" % (self.connection.projectRootFolder, self.frm.cmbProjectFolder.currentText())):
                try:
                    self.connection.sftpClient.mkdir("%s/%s/cookies" % (self.connection.projectRootFolder, self.frm.cmbProjectFolder.currentText()), mode=777)
                except IOError as e:
                    print("some error:: %s", str(e))


            # Submit
            job = Job(connection=self.connection,
                       jobView=self,
                       projectFolder=self.frm.cmbProjectFolder.currentText().strip(),
                       jobID=None,
                       jobName=self.frm.edtJobName.text(),
                       startTime=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                       workerNode=None,
                       port=None,
                       status=0,
                       runTime=self.frm.spinRuntime.value(),
                       nCPU=self.frm.spinNrOfCPU.value(),
                       nGPU=self.frm.spinNrOfGPU.value(),
                       memory=self.frm.spinMemory.value(),
                       singularityImg=self.frm.cmbSingularityImg.currentText().strip(),
                       editor=self.frm.cmbEditor.currentText().strip(),
                       new=True)

            # maybe this one should be run in another thread
            self.connection.submitToQueue(job, self)
            self.frm.accept()

    def __showMessage(self, frm, msgText, msgType):
        if msgType == "error":
            frm.msgBox.setStyleSheet("background-color:red")
        elif msgText == "success":
            frm.msgBox.setStyleSheet("background-color:green")

        frm.msgTxt.setText(msgText)
        frm.msgTxt.adjustSize()


    def showForm(self):


        err = False
        frm = QDialog(self)

        frm.setWindowTitle("Add job")

        frm.resize(1050, 400)
        frm.vLayout = QVBoxLayout(frm)

        ################### Message box for errors #######################
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)

        frm.msgBox = QFrame(frm)
        frm.msgBox.setMinimumHeight(20)
        frm.msgTxt = QLabel(frm.msgBox)
        frm.msgTxt.setFont(font)
        frm.msgTxt.setStyleSheet("color: white")
        frm.vLayout.addWidget(frm.msgBox)

        ################### Group box with new Job #######################
        frm.groupbox = QtWidgets.QGroupBox("New job on %s" % self.connection.connectionName)

        frm.vLayout.addWidget(frm.groupbox)

        frm.frmLayout = QtWidgets.QFormLayout(frm.groupbox)

        # Project folder
        frm.cmbProjectFolder = QComboBox()

        # check if false, then show message.
        # if exists but no subdirs exist ; also show message
        projects = self.connection.getProjects()

        if projects == False:
            self.__showMessage(frm, "Cannot find root folder:\n%s\nCannot load projects or singularity images" % self.connection.projectRootFolder, "error")
            err = True
        elif len(projects) == 0:
            self.__showMessage(frm, "There are no projects in root folder:\n%s\nPlease create one or more subfolders" % self.connection.projectRootFolder, "error")
            err = True
        else:
            for project in self.connection.getProjects():
                frm.cmbProjectFolder.addItem(project)

            index = frm.cmbProjectFolder.findText(self.projectFolder, QtCore.Qt.MatchFixedString)
            if index >= 0:
                frm.cmbProjectFolder.setCurrentIndex(index)
        frm.frmLayout.addRow(QLabel("Project:"), frm.cmbProjectFolder)


        # Jobname
        frm.edtJobName = QLineEdit()
        frm.edtJobName.setMinimumWidth(600)
        frm.edtJobName.setText(self.jobName)
        frm.frmLayout.addRow(QLabel("Job name:"), frm.edtJobName)

        # Runtime
        frm.spinRuntime = QSpinBox()
        frm.spinRuntime.setValue(self.runTime)
        frm.frmLayout.addRow(QLabel("Runtime (hours):"), frm.spinRuntime)

        # Nr of CPU
        frm.spinNrOfCPU = QSpinBox()
        frm.spinNrOfCPU.setValue(self.nCPU)
        frm.frmLayout.addRow(QLabel("# CPU:"), frm.spinNrOfCPU)

        # Nr of GPU
        frm.spinNrOfGPU = QSpinBox()
        if config.JOB_MAX_AMOUNT_OF_GPU == 0:
            frm.spinNrOfGPU.setHidden(True)

        frm.spinNrOfGPU.setValue(self.nGPU)

        if config.JOB_MAX_AMOUNT_OF_GPU > 0:
            frm.frmLayout.addRow(QLabel("# GPU:"), frm.spinNrOfGPU)

        # Memory
        frm.spinMemory = QDoubleSpinBox()
        frm.spinMemory.setValue(self.memory)
        frm.frmLayout.addRow(QLabel("Memory (GB):"), frm.spinMemory)

        # Singularity image
        frm.cmbSingularityImg = QComboBox()

        singularityImages = self.connection.getSingularityImages()
        if singularityImages:
            if len(singularityImages) >= 1:
                for imgName in singularityImages:
                    frm.cmbSingularityImg.addItem(imgName)
                    index = frm.cmbSingularityImg.findText(self.singularityImg, QtCore.Qt.MatchFixedString)
                    if index >= 0:
                        frm.cmbSingularityImg.setCurrentIndex(index)
            elif err == False:
                self.__showMessage(frm, "There are not singularity images in folder %s" % self.connection.projectRootFolder, "error")
        elif err == False:
                self.__showMessage(frm, "The singularity folder\n%s\ndoes not exist" % self.connection.singularityFolder, "error")
        frm.frmLayout.addRow(QLabel("Singularity image:"), frm.cmbSingularityImg)


        # Graphical user interface to program in: currently RServer or Jupterlab
        frm.cmbEditor = QComboBox()
        for editor in self.connection.getEditors():
            frm.cmbEditor.addItem(editor)
            index = frm.cmbEditor.findText(self.editor, QtCore.Qt.MatchFixedString)
            if index >= 0:
                frm.cmbEditor.setCurrentIndex(index)

        frm.frmLayout.addRow(QLabel("Editor:"), frm.cmbEditor)

        ### Buttons
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        frm.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        frm.buttonBox.accepted.connect(self.save)
        frm.buttonBox.rejected.connect(frm.reject)

        frm.vLayout.addWidget(frm.buttonBox)
        frm.setLayout(frm.vLayout)

        return frm

    def __validateForm(self, frm):

        if frm.cmbProjectFolder.currentText().strip() == "" or frm.cmbProjectFolder.currentText() == None:
            self.__showMessage(frm, "Invalid project folder selected", "error")
            return False

        if frm.edtJobName.text().strip() == "" or frm.edtJobName.text() == None:
            self.__showMessage(frm, "Job name cannot be empty", "error")
            return False

        if not isinstance(frm.spinRuntime.value(), int) or frm.spinRuntime.value() < config.JOB_MIN_RUNTIME_HOURS or frm.spinRuntime.value() > config.JOB_MAX_RUNTIME_HOURS:
            self.__showMessage(frm, "Runtime must be between %d and %d hours" % (config.JOB_MIN_RUNTIME_HOURS, config.JOB_MAX_RUNTIME_HOURS), "error")
            return False

        if not isinstance(frm.spinNrOfCPU.value(), int) or frm.spinNrOfCPU.value() < config.JOB_MIN_AMOUNT_OF_CPU or frm.spinNrOfCPU.value() > config.JOB_MAX_AMOUNT_OF_CPU:
            self.__showMessage(frm, "CPU count must be between %d and %d" % (config.JOB_MIN_AMOUNT_OF_CPU, config.JOB_MAX_AMOUNT_OF_CPU), "error")
            return False

        print("receving gpu count ", frm.spinNrOfGPU.value())
        if not isinstance(frm.spinNrOfGPU.value(), int) or frm.spinNrOfGPU.value() < config.JOB_MIN_AMOUNT_OF_GPU or frm.spinNrOfGPU.value() > config.JOB_MAX_AMOUNT_OF_GPU:
            self.__showMessage(frm, "GPU count must be between %d and %d" % (config.JOB_MIN_AMOUNT_OF_GPU, config.JOB_MAX_AMOUNT_OF_GPU), "error")
            return False

        if not isinstance(frm.spinMemory.value(), float) or frm.spinMemory.value() < config.JOB_MIN_AMOUNT_OF_MEMORY_GB or frm.spinRuntime.value() > config.JOB_MAX_AMOUNT_OF_MEMORY_GB:
            self.__showMessage(frm, "Amount of memory must be between %d and %d GB" % (config.JOB_MIN_AMOUNT_OF_MEMORY_GB, config.JOB_MAX_AMOUNT_OF_MEMORY_GB), "error")
            return False

        if frm.cmbSingularityImg.currentText().strip() == "" or frm.cmbSingularityImg.currentText() == None:
            self.__showMessage(frm, "Invalid singularity image selected", "error")
            return False

        # Make sure the project folder still exists
        if not self.connection.file_exists("%s/%s" % (self.connection.projectRootFolder, frm.cmbProjectFolder.currentText())):
            self.__showMessage(frm, "The selected project does not exist anymore", "error")
            return False

        # Make sure that the singularity image still exists
        if not self.connection.file_exists("%s/%s" % (self.connection.singularityFolder, frm.cmbSingularityImg.currentText())):
            self.__showMessage(frm, "The selected singularity image does not exist anymore", "error")
            return False

        return True


    def showList(self):

        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        self.foo = QWidget()
        self.foo.setStyleSheet("background-color:black;")


        self.foo.setGeometry(QtCore.QRect(10, 10, 400, 200))
        self.vLayout = QVBoxLayout(self.foo)

        ### Add label
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label = QLabel()
        self.label.setText("Running jobs:")
        self.label.setFont(font)
        self.vLayout.addWidget(self.label)

        ### Add jobView
        self.jobTable.setModel(self.connection)
        self.jobTable.setShowGrid(False)
        self.jobTable.setAlternatingRowColors(True)
        self.jobTable.setSelectionBehavior(QTableView.SelectRows)
        self.jobTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.jobTable.customContextMenuRequested.connect(self.context_menu)
        self.resizeHeaders()
        self.jobTable.resizeRowsToContents()
        self.jobTable.resizeColumnsToContents()
        self.vLayout.addWidget(self.jobTable)

        ### Buttons
        self.hLayoutWidget = QWidget()
        self.hLayoutWidget.setGeometry(QtCore.QRect(0, 0, 200, 200))
        self.hLayout = QHBoxLayout(self.hLayoutWidget)

        self.addButton = QtWidgets.QPushButton()
        self.addButton.setObjectName("add_job")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(basedir, "add_job_normal.png")), QtGui.QIcon.Normal)
        icon.addPixmap(QtGui.QPixmap(os.path.join(basedir, "add_job_hot.png")), QtGui.QIcon.Active)
        icon.addPixmap(QtGui.QPixmap(os.path.join(basedir, "add_job_disabled.png")), QtGui.QIcon.Disabled)
        self.addButton.setIcon(icon)
        self.addButton.setIconSize(QtCore.QSize(24, 24))
        self.addButton.setText("Add Job")
        self.addButton.installEventFilter(self)
        self.hLayout.addWidget(self.addButton)


        self.deleteAllButton = QtWidgets.QPushButton()
        self.deleteAllButton.setObjectName("delete_jobs")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(os.path.join(basedir, "delete_jobs_normal.png")), QtGui.QIcon.Normal)
        icon1.addPixmap(QtGui.QPixmap(os.path.join(basedir, "delete_jobs_hot.png")), QtGui.QIcon.Active)
        icon1.addPixmap(QtGui.QPixmap(os.path.join(basedir, "delete_jobs_disabled.png")), QtGui.QIcon.Disabled)
        self.deleteAllButton.setIcon(icon1)
        self.deleteAllButton.setIconSize(QtCore.QSize(24, 24))
        self.deleteAllButton.setText("Delete all jobs")
        self.deleteAllButton.installEventFilter(self)
        self.hLayout.addWidget(self.deleteAllButton)

        self.syncButton = QtWidgets.QPushButton()
        self.syncButton.setObjectName("sync_jobs")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(os.path.join(basedir, "sync_jobs_normal.png")), QtGui.QIcon.Normal)
        icon2.addPixmap(QtGui.QPixmap(os.path.join(basedir, "sync_job_hot.png")), QtGui.QIcon.Active)
        icon2.addPixmap(QtGui.QPixmap(os.path.join(basedir, "sync_jobs_disabled.png")), QtGui.QIcon.Disabled)
        self.syncButton.setIcon(icon2)
        self.syncButton.setIconSize(QtCore.QSize(24, 24))
        self.syncButton.setText("Sync jobs")
        self.syncButton.installEventFilter(self)
        self.hLayout.addWidget(self.syncButton)
        self.vLayout.addWidget(self.hLayoutWidget)

        self.label2 = QLabel()
        self.label2.setText("Log output:")
        self.label2.setFont(font)
        self.vLayout.addWidget(self.label2)

        self.logEdit = QTextEdit()
        self.logEdit.setGeometry(QtCore.QRect(0, 0, 800, 400))
        self.logEdit.setReadOnly(True)

        self.spinner = QtWaitingSpinner(self.jobTable)
        self.spinner.setNumberOfLines(18)
        self.spinner.setInnerRadius(12)
        self.spinner.setLineLength(20)
        self.spinner.setLineWidth(5)

        self.vLayout.addWidget(self.logEdit)


        # Buttons handling
        self.addButton.clicked.connect(self.add)
        self.deleteAllButton.pressed.connect(self.deleteAll)
        self.syncButton.pressed.connect(self.sync)

        delegate = ProgressDelegate(self.jobTable)
        self.jobTable.setItemDelegateForColumn(11, delegate)

        self.setLayout(self.vLayout)


    # Change the image from "normal" to "hot" on mouseover
    def eventFilter(self, object, event):

        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        if event.type() == QtCore.QEvent.HoverEnter:
            object.setIcon(QtGui.QIcon(os.path.join(basedir, object.objectName() + "_hot.png")))
        elif event.type() == QtCore.QEvent.HoverLeave:
            object.setIcon(QtGui.QIcon(os.path.join(basedir, object.objectName() + "_normal.png")))

        return False

    def viewUpdateStarted(self):
        self.spinner.start()

    def viewUpdateFinished(self):
        self.spinner.stop()

        self.connection.layoutChanged.emit()
        self.addButton.setEnabled(True)
        self.deleteAllButton.setEnabled(True)
        self.syncButton.setEnabled(True)


    def writeLog(self, msg):
        self.log.writeLine(connectionID=msg['connectionID'], jobID=msg['jobID'], message=msg['message'], messageType=msg['messageType'], show=True)

    def resizeHeaders(self):
        header = self.jobTable.horizontalHeader()

        # Do not make the header bold when an item is selected
        header.setHighlightSections(False)

        for i in range(11):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

        # progress indicator takes rest of available space
        header.setSectionResizeMode(11, QtWidgets.QHeaderView.Stretch)

    def context_menu(self):

        basedir = "icons"
        if getattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        menu = QtWidgets.QMenu()
        add_job = menu.addAction("Add Job")
        add_job.setIcon(QtGui.QIcon(os.path.join(basedir, "add_job_normal.png")))
        add_job.triggered.connect(lambda: self.add())
        if self.jobTable.selectedIndexes():

            rowID = self.jobTable.currentIndex().row()
            jobIDs = list(self.connection.jobs.keys())

            delete_job = menu.addAction("Delete Job")
            delete_job.setIcon(QtGui.QIcon(os.path.join(basedir, "delete_jobs_normal.png")))
            delete_job.triggered.connect(lambda: self.delete(self.jobTable.currentIndex()))

            browse_job = menu.addAction("Open job in browser window")
            browse_job.setIcon(QtGui.QIcon(os.path.join(basedir, "weblink_32px.png")))
            browse_job.triggered.connect(lambda: self.browse(self.jobTable.currentIndex()))

            if self.connection.jobs[jobIDs[rowID]].status != 1:
                browse_job.setDisabled(True)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def sync(self):
        # this model should be made in the constructor i think
        self.connection.syncJobs()
        self.connection.layoutChanged.emit() ###




    def browse(self, index):

        # 1; the open tunnel should be a property of the job
        # 2 we can get the job by the ID

        jobIDs = list(self.connection.jobs.keys())
        job = self.connection.jobs[jobIDs[index.row()]]

        # atually only open iof not already opened
        job.openSSHTunnel(self)
        webbrowser.open_new_tab("http://localhost:%d" % int(job.port))

    def delete(self, index):
        jobIDs = list(self.connection.jobs.keys())
        job = self.connection.jobs[jobIDs[index.row()]]

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)

        msg.setText("Delete job %s (%d)?" % (job.jobName, job.jobID))
        msg.setInformativeText("Unsaved work will be lost!")
        msg.setWindowTitle("Delete Job")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if msg.exec() == QMessageBox.Ok:
            job.closeSSHTunnel(self)
            self.connection.deleteJob(job.jobID)

    def deleteAll(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)

        msg.setText("Delete all jobs?")
        msg.setInformativeText("Unsaved work will be lost!")
        msg.setWindowTitle("Delete jobs")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Ok:
            self.connection.deleteAllJobs()