import os
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QLabel, QLineEdit, \
        QGroupBox, QDialog, QComboBox, QHBoxLayout, QRadioButton, QFrame, QDialogButtonBox, QSpinBox, QDoubleSpinBox
from sshconf import read_ssh_config
from PyQt5 import QtGui, QtCore
from connections import Connection
import config

class FormJob(QDialog):

    def __init__(self, *args, **kwargs):
        super(FormJob, self).__init__(*args)

        self.dbTable = config.DB.table("jobs")

        self.setWindowTitle("Add job")
        self.connection = kwargs['connection']

        # Set fields
        self.jobID = kwargs['jobID']
        self.jobName = kwargs['jobName']
        self.projectFolder = kwargs['projectFolder']
        self.runtime = kwargs['runtime']
        self.nCPU = kwargs['nCPU']
        self.nGPU = kwargs['nGPU']
        self.memory = kwargs['memory']
        self.singularityImg = kwargs['singularityImg']


    #    self.setupUi()


    # Make this function showForm or something like that
    def showForm(self):
        self.resize(800, 470)
        self.vLayout = QVBoxLayout(self)
        self.groupbox = QGroupBox("New job on %s" % self.connection.connectionName)

        self.vLayout.addWidget(self.groupbox)

        self.frmLayout = QFormLayout(self.groupbox)

        # Project folder
        self.cmbProjectFolder = QComboBox()


        # check if false, then show message.
        # if exists but no subdirs exist ; also show message
        for project in self.connection.getProjects():
            self.cmbProjectFolder.addItem(project)

        index = self.cmbProjectFolder.findText(self.projectFolder, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cmbProjectFolder.setCurrentIndex(index)
        self.frmLayout.addRow(QLabel("Project:"), self.cmbProjectFolder)

        # Jobname
        self.edtJobName = QLineEdit()
        self.edtJobName.setText(self.jobName)
        self.frmLayout.addRow(QLabel("Job name:"), self.edtJobName)

        # Runtime
        self.spinRuntime = QSpinBox()
        self.spinRuntime.setRange(1, 96)
        self.spinRuntime.setValue(self.runtime)
        self.frmLayout.addRow(QLabel("Runtime (hours):"), self.spinRuntime)

        # Nr of CPU
        self.spinNrOfCPU = QSpinBox()
        self.spinNrOfCPU.setValue(self.nCPU)
        self.spinRuntime.setRange(1, 40)
        self.frmLayout.addRow(QLabel("# CPU:"), self.spinNrOfCPU)

        # Nr of GPU
        self.spinNrOfGPU = QSpinBox()
        self.spinNrOfGPU.setValue(self.nGPU)
        self.spinRuntime.setRange(1, 4)
        self.frmLayout.addRow(QLabel("# GPU:"), self.spinNrOfGPU)

        # Memory
        self.spinMemory = QDoubleSpinBox()
        self.spinMemory.setValue(self.memory)
        self.spinRuntime.setRange(1.0, 256.0)
        self.frmLayout.addRow(QLabel("Memory (GB):"), self.spinMemory)

        # Singularity image
        self.cmbSingularityImg = QComboBox()
        for imgName in self.connection.getSingularityImages():
            self.cmbSingularityImg.addItem(imgName)

        index = self.cmbSingularityImg.findText(self.singularityImg, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cmbSingularityImg.setCurrentIndex(index)
        self.frmLayout.addRow(QLabel("Singularity image:"), self.cmbSingularityImg)


        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)
