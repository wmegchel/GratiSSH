import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import  *
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError, HandlerSSHTunnelForwarderError
import config


class JobForm(QDialog):

    def __init__(self, job, edit=True):
        super(JobForm, self).__init__()
        self.job = job

        if edit:
            self.showForm()
        else:
            self.jobDetails()

    def showForm(self):
        err = False

        self.setWindowTitle("Add job")

        self.resize(1050, 400)
        vLayout = QVBoxLayout(self)

        ################### Message box for errors #######################
        font = QFont()
        font.setBold(True)
        font.setWeight(75)

        self.msgBox = QFrame(self)
        self.msgBox.setMinimumHeight(20)
        self.msgTxt = QLabel(self.msgBox)
        self.msgTxt.setFont(font)
        self.msgTxt.setStyleSheet("color: white")
        vLayout.addWidget(self.msgBox)

        ################### Group box with new Job #######################
        groupbox = QGroupBox("New job on %s" % self.job.connection.connectionName)

        vLayout.addWidget(groupbox)

        frmLayout = QFormLayout(groupbox)

        # Project folder
        self.cmbProjectFolder = QComboBox()

        # check if false, then show message.
        # if exists but no subdirs exist ; also show message
        projects = self.job.connection.getProjects()

        if projects == False:
            self.showMsg("Cannot find root folder:\n%s\nCannot load projects or singularity images" % self.job.connection.projectRootFolder,"error")
            err = True
        elif len(projects) == 0:
            self.showMsg("There are no projects in root folder:\n%s\nPlease create one or more subfolders" % self.job.connection.projectRootFolder, "error")
            err = True
        else:
            for project in self.job.connection.getProjects():
                self.cmbProjectFolder.addItem(project)

            index = self.cmbProjectFolder.findText(self.job.projectFolder, Qt.MatchFixedString)
            if index >= 0:
                self.cmbProjectFolder.setCurrentIndex(index)
        frmLayout.addRow(QLabel("Project:"), self.cmbProjectFolder)

        # Jobname
        self.edtJobName = QLineEdit(self.job.jobName)
        self.edtJobName.setMinimumWidth(600)
        frmLayout.addRow(QLabel("Job name:"), self.edtJobName)

        # Runtime
        self.spinRuntime = QSpinBox()
        self.spinRuntime.setValue(self.job.runTime)
        frmLayout.addRow(QLabel("Runtime (hours):"), self.spinRuntime)

        # Nr of CPU
        self.spinNrOfCPU = QSpinBox()
        self.spinNrOfCPU.setValue(self.job.nCPU)
        frmLayout.addRow(QLabel("# CPU:"), self.spinNrOfCPU)

        # Nr of GPU
        self.spinNrOfGPU = QSpinBox()
        if config.JOB_MAX_AMOUNT_OF_GPU == 0:
            self.spinNrOfGPU.setHidden(True)

        self.spinNrOfGPU.setValue(self.job.nGPU)

        if config.JOB_MAX_AMOUNT_OF_GPU > 0:
            frmLayout.addRow(QLabel("# GPU:"), self.spinNrOfGPU)

        # Memory
        self.spinMemory = QDoubleSpinBox()
        self.spinMemory.setValue(self.job.memory)
        frmLayout.addRow(QLabel("Memory (GB):"), self.spinMemory)

        # Singularity image
        self.cmbSingularityImg = QComboBox()

        singularityImages = self.job.connection.getSingularityImages()
        if singularityImages:
            if len(singularityImages) >= 1:
                for imgName in singularityImages:
                    self.cmbSingularityImg.addItem(imgName)
                    index = self.cmbSingularityImg.findText(self.job.singularityImg, Qt.MatchFixedString)
                    if index >= 0:
                        self.cmbSingularityImg.setCurrentIndex(index)
            elif err == False:
                self.showMsg("There are not singularity images in folder %s" % self.job.connection.projectRootFolder,
                                   "error")
        elif err == False:
            self.showMsg("The singularity folder\n%s\ndoes not exist" % self.job.connection.singularityFolder, "error")
        frmLayout.addRow(QLabel("Singularity image:"), self.cmbSingularityImg)

        # Graphical user interface to program in: currently RServer or Jupterlab
        self.cmbEditor = QComboBox()
        for editor in self.job.connection.getEditors():
            self.cmbEditor.addItem(editor)
            index = self.cmbEditor.findText(self.job.editor, Qt.MatchFixedString)
            if index >= 0:
                self.cmbEditor.setCurrentIndex(index)

        frmLayout.addRow(QLabel("Editor:"), self.cmbEditor)

        ### Buttons
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.validate)
        self.buttonBox.rejected.connect(self.reject)

        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)

    def validate(self):
        if self.cmbProjectFolder.currentText().strip() == "" or self.cmbProjectFolder.currentText() == None:
            self.showMsg("Invalid project folder selected", "error")
            return False

        if self.edtJobName.text().strip() == "" or self.edtJobName.text() == None:
            self.showMsg("Job name cannot be empty", "error")
            return False

        if not isinstance(self.spinRuntime.value(), int) or self.spinRuntime.value() < config.JOB_MIN_RUNTIME_HOURS or self.spinRuntime.value() > config.JOB_MAX_RUNTIME_HOURS:
            self.showMsg("Runtime must be between %d and %d hours" % (config.JOB_MIN_RUNTIME_HOURS, config.JOB_MAX_RUNTIME_HOURS), "error")
            return False

        if not isinstance(self.spinNrOfCPU.value(),int) or self.spinNrOfCPU.value() < config.JOB_MIN_AMOUNT_OF_CPU or self.spinNrOfCPU.value() > config.JOB_MAX_AMOUNT_OF_CPU:
            self.showMsg("CPU count must be between %d and %d" % (config.JOB_MIN_AMOUNT_OF_CPU, config.JOB_MAX_AMOUNT_OF_CPU), "error")
            return False

        if not isinstance(self.spinNrOfGPU.value(), int) or self.spinNrOfGPU.value() < config.JOB_MIN_AMOUNT_OF_GPU or self.spinNrOfGPU.value() > config.JOB_MAX_AMOUNT_OF_GPU:
            self.showMsg("GPU count must be between %d and %d" % (config.JOB_MIN_AMOUNT_OF_GPU, config.JOB_MAX_AMOUNT_OF_GPU), "error")
            return False

        if not isinstance(self.spinMemory.value(),float) or self.spinMemory.value() < config.JOB_MIN_AMOUNT_OF_MEMORY_GB or self.spinRuntime.value() > config.JOB_MAX_AMOUNT_OF_MEMORY_GB:
            self.showMsg("Amount of memory must be between %d and %d GB" % (config.JOB_MIN_AMOUNT_OF_MEMORY_GB, config.JOB_MAX_AMOUNT_OF_MEMORY_GB), "error")
            return False

        if self.cmbSingularityImg.currentText().strip() == "" or self.cmbSingularityImg.currentText() == None:
            self.showMsg("Invalid singularity image selected", "error")
            return False

        # Make sure the project folder still exists
        if not self.job.connection.file_exists("%s/%s" % (self.job.connection.projectRootFolder, self.cmbProjectFolder.currentText())):
            self.showMsg("The selected project does not exist anymore", "error")
            return False

        # Make sure that the singularity image still exists
        if not self.job.connection.file_exists("%s/%s" % (self.job.connection.singularityFolder, self.cmbSingularityImg.currentText())):
            self.showMsg("The selected singularity image does not exist anymore", "error")
            return False

        # Check if the cookies folder exists; if not make it
        if not self.job.connection.file_exists("%s/%s/cookies" % (self.job.connection.projectRootFolder, self.cmbProjectFolder.currentText())):
            try:
                self.job.connection.sftpClient.mkdir("%s/%s/cookies" % (self.job.connection.projectRootFolder, self.cmbProjectFolder.currentText()), mode=777)
            except IOError as e:
                print("Uknown IOError:: %s", str(e))

        self.accept()

        return True


    def showMsg(self, msgText, msgType):
        if msgType == "error":
            self.msgBox.setStyleSheet("background-color:red")
        elif msgText == "success":
            self.msgBox.setStyleSheet("background-color:green")

        self.msgTxt.setText(msgText)
        self.msgTxt.adjustSize()


    def jobDetails(self):
        self.setWindowTitle("Job details")

        self.resize(1050, 400)
        vLayout = QVBoxLayout(self)

        ################### Group box with new Job #######################
        groupbox = QGroupBox("Job %s" % self.job.jobName)
        vLayout.addWidget(groupbox)

        frmLayout = QFormLayout(groupbox)

        project = QLabel("Project:")
        jobName = QLabel("Job name:")
        runTime = QLabel("Runtime (hours):")
        nCPU = QLabel("# CPU:")
        nGPU = QLabel("# GPU:")
        mem = QLabel("Memory (GB):")
        si = QLabel("Singularity image:")
        editor = QLabel("Editor:")

        bold = QFont()
        bold.setBold(True)
        project.setFont(bold)
        jobName.setFont(bold)
        runTime.setFont(bold)
        nCPU.setFont(bold)
        nGPU.setFont(bold)
        mem.setFont(bold)
        si.setFont(bold)
        editor.setFont(bold)

        frmLayout.addRow(project, QLabel(self.job.connection.projectRootFolder + "/" + self.job.projectFolder))
        frmLayout.addRow(jobName, QLabel(self.job.jobName))
        frmLayout.addRow(runTime, QLabel(str(self.job.runTime)))
        frmLayout.addRow(nCPU, QLabel(str(self.job.nCPU)))
        frmLayout.addRow(nGPU, QLabel(str(self.job.nGPU)))
        frmLayout.addRow(mem, QLabel(str(self.job.memory)))
        frmLayout.addRow(si, QLabel(self.job.singularityImg))
        frmLayout.addRow(editor, QLabel(self.job.editor))

        ### Buttons
        QBtn = QDialogButtonBox.Ok #  | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        #self.buttonBox.rejected.connect(self.reject)

        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)
