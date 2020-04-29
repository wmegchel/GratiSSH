# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'new_job.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QDialog, QSpinBox, QDoubleSpinBox, QComboBox, QTimeEdit, QVBoxLayout
from tinydb import TinyDB, where
import re
import random


class Job(QDialog):

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args)

        db = TinyDB('/home/wmegchel/tinydb.json')
        self.dbTable = db.table('jobs')

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
        self.groupbox = QtWidgets.QGroupBox("New job on %s" % self.connection.connectionName)

        self.vLayout.addWidget(self.groupbox)

        self.frmLayout = QtWidgets.QFormLayout(self.groupbox)

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
        self.spinRuntime.setValue(self.runtime)
        self.frmLayout.addRow(QLabel("Runtime (hours):"), self.spinRuntime)

        # Nr of CPU
        self.spinNrOfCPU = QSpinBox()
        self.spinNrOfCPU.setValue(self.nCPU)
        self.frmLayout.addRow(QLabel("# CPU:"), self.spinNrOfCPU)

        # Nr of GPU
        self.spinNrOfGPU = QSpinBox()
        self.spinNrOfGPU.setValue(self.nGPU)
        self.frmLayout.addRow(QLabel("# GPU:"), self.spinNrOfGPU)

        # Memory
        self.spinMemory = QDoubleSpinBox()
        self.spinMemory.setValue(self.memory)
        self.frmLayout.addRow(QLabel("Memory (GB):"), self.spinMemory)

        # Singularity image
        self.cmbSingularityImg = QComboBox()
        for imgName in self.connection.getSingularityImages():
            self.cmbSingularityImg.addItem(imgName)

        index = self.cmbSingularityImg.findText(self.singularityImg, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cmbSingularityImg.setCurrentIndex(index)
        self.frmLayout.addRow(QLabel("Singularity image:"), self.cmbSingularityImg)





        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)


    def getAll(self):
        return self.dbTable.search(where('connectionID') == self.connectionID)


    def validate(self):

        # jobname
        # project folder set and present, as well as cookies subdir present
        # runtime > 0.01 and < 23
        # cpu >1 <= 20
        # gpu (hide for now)
        # memory: (1GB - 12GB)
        # singularity image present


        print("validationg jobs")
        self.connection.file_exists()
        return True

    # Save job to DB
    def save(self):
        print("saving job %s to DB" % self.jobID)
        return True

