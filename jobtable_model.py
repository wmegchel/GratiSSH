from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from jobtable_view import JobTableView
import config
import os, sys
from random import randint
from job import Job


class JobTableModel(QAbstractTableModel):

    msgSignal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # Start a threadpool for job submission and synchronizing
        self.jobs = {}

     #   self.tblJobs = config.DB.table('jobs')
        #self.threadpool = QThreadPool()
        #  # not needed!

#        self.timer = QTimer()
#        self.timer.setInterval(config.SYNC_JOBS_WITH_SERVER_INTERVAL_SECONDS * 1000)  # msec
 #       self.timer.timeout.connect(self.syncJobs)



        self.colHeaders = ["JobID", "Job name", "Project", "Start time", "Runtime", "#CPU", "#GPU", "RAM", "Node",
                            "Singularity img", "", "Time left"]
        self.columns = ["jobID", "jobName", "projectFolder", "startTime", "runTime", "nCPU", "nGPU", "memory",
                        "workerNode", "singularityImg", "status", "time_left"]

        #self.jobs = {}

    @pyqtSlot(dict)
    def setJobs(self, jobs):
        self.jobs = jobs

    @pyqtSlot(Job)
    def addJob(self, job):
#        for attr, value in job.__dict__.items():
#            print(attr, value)


        self.jobs[job.jobID] = job

    @pyqtSlot(int)
    def deleteJob(self, jobID):
        del self.jobs[jobID]

#
# you should remove the jobs property copletely from the jobList and add it to jobModel

    def data(self, index, role):
       # print("does someting go wriong here .... ")
        col = self.columns[index.column()]
        jobIDs = list(self.jobs.keys())

        #print("jobs arriving in data :: ")
        #print(jobIDs)

        if role == Qt.DisplayRole and col not in ["status", "time_left"]:
            value = getattr(self.jobs[jobIDs[index.row()]], col)
            if col == "startTime" and value is not None:
                value = value[11:16]
            elif col == "memory":
                value = str(value) + "G"

            return value

        elif role == Qt.TextAlignmentRole and col not in ["status", "time_left"]:
            value = getattr(self.jobs[jobIDs[index.row()]], col)

            if isinstance(value, int) or isinstance(value, float):
                return Qt.AlignVCenter + Qt.AlignRight
            else:
                return Qt.AlignVCenter + Qt.AlignLeft

        elif role == Qt.DecorationRole and col == "status":

            basedir = "icons"
            if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
                basedir = os.path.join(sys._MEIPASS, "icons")

            value = getattr(self.jobs[jobIDs[index.row()]], col)
            if value == 0:
                return QPixmap(os.path.join(basedir, "stopwatch_24px.png"))
            elif value == 1:
                if getattr(self.jobs[jobIDs[index.row()]], "editor") == "Rserver":
                    return QPixmap(os.path.join(basedir, "rserver_24px.png"))
                else:
                    return QPixmap(os.path.join(basedir, "jupyterlab_24px.png"))


    def rowCount(self, index):
        return len(self.jobs)

    def columnCount(self, index):
        return len(self.columns)

    def headerData(self, colID, orientation, role=Qt.DisplayRole):
        # colheader can be set here
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.colHeaders[colID]






