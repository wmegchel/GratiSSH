from datetime import datetime
import config
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from waitingspinnerwidget import QtWaitingSpinner
import webbrowser
from logger import Logger
import sys
import os
from job import Job
from jobtable_model import JobTableModel
from jobtable_view import JobTableView
from job_form import JobForm
from ssh_worker import Worker, WorkerSignals
from job_queue import JobQueue


class JobList(QWidget):

    def __init__(self, connection):
        super(JobList, self).__init__()
        self.connection = connection
        self.jobTableModel = JobTableModel()
        self.jobTableView = JobTableView(self.jobTableModel)
        self.dbTable = config.DB.table("jobs")
        self.log = Logger(jobList=self)
        self.tunnels = {}
        self.threadpool = QThreadPool()

        # Waiting spinner
        self.spinner = QtWaitingSpinner(self.jobTableView)
        self.spinner.setNumberOfLines(18)
        self.spinner.setInnerRadius(12)
        self.spinner.setLineLength(20)
        self.spinner.setLineWidth(5)

        self.listJobs()


    def listJobs(self):

        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        self.vLayout = QVBoxLayout()

        ### Add label
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.labelJobs = QLabel("Jobs (%d)" % len(self.jobTableModel.jobs))
        self.labelJobs.setFont(font)
        self.vLayout.addWidget(self.labelJobs)

        ### Add jobView
        self.jobTableView.setView()
        self.vLayout.addWidget(self.jobTableView)

        ### Buttons
        hLayoutWidget = QWidget()
        hLayoutWidget.setGeometry(QRect(0, 0, 200, 200))
        hLayout = QHBoxLayout(hLayoutWidget)

        # Add job
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(basedir, "add_job_normal.png")), QIcon.Normal)
        icon.addPixmap(QPixmap(os.path.join(basedir, "add_job_hot.png")), QIcon.Active)
        icon.addPixmap(QPixmap(os.path.join(basedir, "add_job_disabled.png")), QIcon.Disabled)

        self.addButton = QPushButton("Add Job")
        self.addButton.setObjectName("add_job")
        self.addButton.setIcon(icon)
        self.addButton.setIconSize(QSize(24, 24))
        self.addButton.installEventFilter(self)
        self.addButton.setEnabled(False)
        hLayout.addWidget(self.addButton)

        # Delete job
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(os.path.join(basedir, "delete_jobs_normal.png")), QIcon.Normal)
        icon1.addPixmap(QPixmap(os.path.join(basedir, "delete_jobs_hot.png")), QIcon.Active)
        icon1.addPixmap(QPixmap(os.path.join(basedir, "delete_jobs_disabled.png")), QIcon.Disabled)

        self.deleteAllButton = QPushButton("Delete all jobs")
        self.deleteAllButton.setObjectName("delete_jobs")
        self.deleteAllButton.setIcon(icon1)
        self.deleteAllButton.setIconSize(QSize(24, 24))
        self.deleteAllButton.installEventFilter(self)
        self.deleteAllButton.setEnabled(False)
        hLayout.addWidget(self.deleteAllButton)

        # syncButton
        icon2 = QIcon()
        icon2.addPixmap(QPixmap(os.path.join(basedir, "sync_jobs_normal.png")), QIcon.Normal)
        icon2.addPixmap(QPixmap(os.path.join(basedir, "sync_job_hot.png")), QIcon.Active)
        icon2.addPixmap(QPixmap(os.path.join(basedir, "sync_jobs_disabled.png")), QIcon.Disabled)

        self.syncButton = QPushButton("Sync jobs")
        self.syncButton.setObjectName("sync_jobs")
        self.syncButton.setIcon(icon2)
        self.syncButton.setIconSize(QSize(24, 24))
        self.syncButton.installEventFilter(self)
        self.syncButton.setEnabled(False)
        hLayout.addWidget(self.syncButton)

        # clearLogButton
        icon3 = QIcon()
        icon3.addPixmap(QPixmap(os.path.join(basedir, "clear_log_normal.png")), QIcon.Normal)
        icon3.addPixmap(QPixmap(os.path.join(basedir, "clear_log_hot.png")), QIcon.Active)
        icon3.addPixmap(QPixmap(os.path.join(basedir, "clear_log_disabled.png")), QIcon.Disabled)

        self.clearLogButton = QPushButton("Clear log")
        self.clearLogButton.setObjectName("clear_log")
        self.clearLogButton.setIcon(icon3)
        self.clearLogButton.setIconSize(QSize(24, 24))
        self.clearLogButton.installEventFilter(self)
        self.clearLogButton.setEnabled(False)
        hLayout.addWidget(self.clearLogButton)

        self.vLayout.addWidget(hLayoutWidget)






        # Log
        labelLogOutput = QLabel("Log output:")
        labelLogOutput.setFont(font)
        self.vLayout.addWidget(labelLogOutput)

        # Log edit box
        self.logEdit = QTextEdit()
        self.logEdit.setGeometry(QRect(0, 0, 800, 400))
        self.logEdit.setReadOnly(True)
        self.vLayout.addWidget(self.logEdit)

        # Button handling
        self.addButton.clicked.connect(self.addJob)
        self.deleteAllButton.pressed.connect(self.confirmDeleteAllJobs)
        self.syncButton.pressed.connect(self.syncJobs)
        self.clearLogButton.pressed.connect(self.clearLog)

        self.setLayout(self.vLayout)


    def clearLog(self):
        self.logEdit.clear()

    def syncJobs(self):
        # Start a worker that calls the __connect function and
        # synchronizes the jobs running on the server

        #print("JOBLIST -> syncJobs")
        Q = JobQueue.getQueueObject(self.connection)

        # connect to host
        worker = Worker(Q.syncJobs, task="sync")
        worker.signals.updateStarted.connect(self.updateStarted)
        worker.signals.progress.connect(self.writeLog)
        worker.signals.jobsSynced.connect(self.jobTableModel.setJobs)
        worker.signals.updateFinished.connect(self.updateFinished)

        #print("starting worker")
        # Execute job
        self.threadpool.start(worker)
        #print("emit layout changed")

    def addJob(self):
        frm = JobForm(Job(connection=self.connection))
        frm.setModal(True)
        if frm.exec():

            # Submit
            job = Job(connection=self.connection,
                      jobID=0,
                      jobName=frm.edtJobName.text(),
                      projectFolder=frm.cmbProjectFolder.currentText().strip(),
                      startTime=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                      runTime=frm.spinRuntime.value(),
                      nCPU=frm.spinNrOfCPU.value(),
                      nGPU=frm.spinNrOfGPU.value(),
                      memory=frm.spinMemory.value(),
                      singularityImg=frm.cmbSingularityImg.currentText().strip(),
                      workerNode=None,
                      status=0,
                      editor=frm.cmbEditor.currentText().strip(),
                      port=None)

            #print(" >> submitting job now!!!! << ")
            self.submitJob(job)


    def viewJob(self, jobID):
        frm = JobForm(self.jobTableModel.jobs[jobID], edit=False)
        frm.setModal(True)
        frm.exec()


    def submitJob(self, job):

        #print("calling elvis .. the worker")
        Q = JobQueue.getQueueObject(self.connection)

        worker = Worker(Q.submitJob, job=job, task="submit")

        # make
        # worker = Worker(self.__submit, job)
        worker.signals.updateStarted.connect(self.updateStarted)
        worker.signals.progress.connect(self.writeLog)
        worker.signals.jobSubmitted.connect(self.jobTableModel.addJob)
        worker.signals.updateFinished.connect(self.updateFinished)

        self.threadpool.start(worker)

    # @pyqtSlot(Job)
    # def appendJobToList(self, job):
    #     self.jobs[job.jobID] = job

    def confirmDeleteJob(self, index):
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

    def confirmDeleteAllJobs(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)

        msg.setText("Delete all jobs?")
        msg.setInformativeText("Unsaved work will be lost!")
        msg.setWindowTitle("Delete jobs")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Ok:
            self.deleteAllJobs()


    def deleteAllJobs(self):
        for jobID in self.jobTableModel.jobs:
            self.deleteJob(jobID)



    def deleteJob(self, jobID):
        try:
            #print("joblist -> DELETE JOB")

            # part of the queue => this should use Factory design
            Q = JobQueue.getQueueObject(self.connection)

            worker = Worker(Q.deleteJob, jobID=jobID, task="delete")
            worker.signals.updateStarted.connect(self.updateStarted)
            worker.signals.progress.connect(self.writeLog)
            worker.signals.jobDeleted.connect(self.jobTableModel.deleteJob)
            worker.signals.updateFinished.connect(self.updateFinished)

            # Execute job
            self.threadpool.start(worker)
        except:
            self.msgSignal.emit({'connectionID': self.connectionID,
                                 'jobID': jobID,
                                 'message': str(sys.exc_info()[1]),
                                 'messageType': 'ERROR'})



    def updateStarted(self):
        self.addButton.setEnabled(False)
        self.deleteAllButton.setEnabled(False)
        self.syncButton.setEnabled(False)
        self.clearLogButton.setEnabled(False)

        self.spinner.start()


    def updateFinished(self):
        self.spinner.stop()

        self.labelJobs.setText("Jobs (%d)" % len(self.jobTableModel.jobs))
        self.jobTableModel.layoutChanged.emit()
        self.addButton.setEnabled(True)
        self.deleteAllButton.setEnabled(True)
        self.syncButton.setEnabled(True)
        self.clearLogButton.setEnabled(True)


    def writeLog(self, msg):
        self.log.writeLine(connectionID=msg['connectionID'], jobID=msg['jobID'], message=msg['message'],
                           messageType=msg['messageType'], show=True)


    def browse(self, jobID):
        job = self.jobTableModel.jobs[jobID]
        res = job.openSSHTunnel(self)
        if res == True:
            webbrowser.open_new_tab("http://localhost:%d" % int(job.port))
        else:
            self.log.writeLine(connectionID=self.connection.connectionID, jobID=jobID, message=res, messageType="ERR", show=True)


    # Change the image from "normal" to "hot" on mouseover
    def eventFilter(self, object, event):

        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        if event.type() == QEvent.HoverEnter:
            object.setIcon(QIcon(os.path.join(basedir, object.objectName() + "_hot.png")))
        elif event.type() == QEvent.HoverLeave:
            object.setIcon(QIcon(os.path.join(basedir, object.objectName() + "_normal.png")))

        return False