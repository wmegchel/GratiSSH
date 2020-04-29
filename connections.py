from tinydb import TinyDB, Query, where
import paramiko
import os
import stat
from paramiko.ssh_exception import SSHException
from paramiko.sftp_client import SFTPError, SFTP_NO_SUCH_FILE
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from sshconf import read_ssh_config

import config
from job_model import Job
from logger import Logger
import xml.etree.ElementTree as ET
import math
from random import randint
import re, sys
from waitingspinnerwidget import QtWaitingSpinner
import time
from datetime import datetime

class WorkerSignals(QObject):

    viewUpdateStarted = pyqtSignal()
    viewUpdateFinished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(dict)



class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn

        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):

        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.signals.viewUpdateStarted.emit()

            result = self.fn(self, *self.args, **self.kwargs)
        except:
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.viewUpdateFinished.emit()  # Done


class Connection(QAbstractTableModel):

    msgSignal = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args)

        # Start a threadpool for job submission and synchronizing
        self.threadpool = QThreadPool()
        self.tblConnections = config.DB.table('connections')
        self.tblJobs = config.DB.table('jobs')
        self.jobs = {}

        if "connectionID" in kwargs.keys():
            self.connectionID = kwargs['connectionID']
#            self.logger = Logger(connection=self)

            if "update" in kwargs.keys() and kwargs['update'] is True:
                self.connectionName = kwargs['connectionName']
                self.hostName = kwargs['hostName']
                self.passphrase = kwargs['passphrase']
                self.gridEngine = kwargs['gridEngine']
                self.singularityFolder = kwargs['singularityFolder']
                self.projectRootFolder = kwargs['projectRootFolder']
            else:
                self.__get()
                self.timer = QTimer()
                self.timer.setInterval(config.SYNC_JOBS_WITH_SERVER_INTERVAL_SECONDS * 1000) # msec
                self.timer.timeout.connect(self.syncJobs)

        else:
            self.connectionID = None
            self.connectionName = ""
            self.passphrase = ""
            self.hostName = ""
            self.gridEngine = ""
            self.singularityFolder = ""
            self.projectRootFolder = ""

        self.sshClient = paramiko.SSHClient()
        self.colHeaders = ["JobID", "Job name", "Project", "Start time", "Runtime", "#CPU", "#GPU", "RAM", "Node", "Singularity img", "", "Time left"]
        self.columns = ["jobID", "jobName", "projectFolder", "startTime", "runTime", "nCPU", "nGPU", "memory", "workerNode", "singularityImg", "status", "time_left"]


    def data(self, index, role):
        col = self.columns[index.column()]
        jobIDs = list(self.jobs.keys())

        if role == Qt.DisplayRole and col not in ["status", "time_left"]:
            value = getattr(self.jobs[jobIDs[index.row()]], col)
            if col == "startTime" and value is not None:
                value = value[11:16]

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


    def saveJobToDB(self, job):
        #self.progress.connect(self.jobView.writeLog)

        try:
            self.tblJobs.insert({'connectionID': job.connection.connectionID,
                                 "jobID": job.jobID,
                                 'projectFolder': job.projectFolder,
                                 'jobName': job.jobName,
                                 'runTime': job.runTime,
                                 'startTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 'status': 0,
                                 "nCPU": job.nCPU,
                                 'nGPU': job.nGPU,
                                 'memory': job.memory,
                                 'singularityImg': job.singularityImg,
                                 'workerNode': None,
                                 'port': None,
                                 'editor': job.editor})
        except:
            self.msgSignal.emit({'connectionID': self.connectionID, 'jobID': None, 'message': str(sys.exc_info()[1]), 'messageType': 'ERROR'})

        # add the job without querying the DB
        self.jobs[job.jobID] = job


    def getJobsFromDB(self):
        try:
            # Get jobs from DB and create list of job objects
            self.jobs = {}
            for job in self.tblJobs.search(where('connectionID') == self.connectionID):
                self.jobs[job['jobID']] = Job(connection=self,
                                               connectionID=job['connectionID'],
                                               jobID=job['jobID'],
                                               projectFolder=job['projectFolder'],
                                               jobName=job['jobName'],
                                               runTime=job['runTime'],
                                               startTime=job['startTime'],
                                               status=job['status'],
                                               nCPU=job['nCPU'],
                                               nGPU=job['nGPU'],
                                               memory=job['memory'],
                                               workerNode = job['workerNode'],
                                               port = job['port'],
                                               singularityImg=job['singularityImg'],
                                               editor=job['editor'])
        except:
            # emit a signal to the logger
            self.msgSignal.emit({'connectionID': self.connectionID, 'jobID': 0, 'message': str(sys.exc_info()[1]), 'messageType': 'ERROR'})

        self.msgSignal.emit({'connectionID': self.connectionID, 'jobID': 0, 'message': 'jobs loaded', 'messageType': 'INFO'})



    def delete(self):
        self.tblConnections.remove(where('connectionID') == self.connectionID)

    def deleteAllJobs(self):
        for jobID in list(self.jobs.keys()):
            self.deleteJob(jobID)


    def deleteJob(self, jobID):
        try:
            # remove from DB
            self.tblJobs.remove((where('connectionID') == self.connectionID) & (where('jobID') == jobID))
            # self.layoutChanged.emit()

            # remove from dictionary
            del self.jobs[jobID]

            worker = Worker(self.__killJob, jobID=jobID)
            worker.signals.viewUpdateStarted.connect(self.jobView.viewUpdateStarted)
            worker.signals.progress.connect(self.jobView.writeLog)
            worker.signals.viewUpdateFinished.connect(self.jobView.viewUpdateFinished)

            # Execute job
            self.threadpool.start(worker)
        except:
            self.msgSignal.emit({'connectionID': self.connectionID,
                                'jobID': jobID,
                                'message': str(sys.exc_info()[1]),
                                'messageType': 'ERROR'})

    def __killJob(self, worker, *args, **kwargs):
        jobID = kwargs['jobID']

        try:
            # send qdel command
            self.exec_cmd("qdel %d" % int(jobID))

            # update log
            worker.signals.progress.emit({'connectionID': self.connectionID,
                                'jobID': jobID,
                                'message': "Job %d deleted" % jobID,
                                'messageType': 'SUCCESS'})
        except KeyError as e:
            worker.signals.progress.emit({'connectionID': self.connectionID,
                                'jobID': jobID,
                                'message': str(e),
                                'messageType': 'ERROR'})
        except:
            worker.signals.progress.emit({'connectionID': self.connectionID,
                                'jobID': jobID,
                                'message': str(sys.exc_info()[1]),
                                'messageType': 'ERROR'})

    def connect_and_sync(self, worker, *args, **kwargs):
        self.__connect(worker, *args, **kwargs)
        self.__sync(worker, *args, **kwargs)

    def setJobView(self, jobView):
        self.jobView = jobView


    def connectToHost(self):
        # Start a worker that calls the __connect function and
        # synchronizes the jobs running on the server
        worker = Worker(self.connect_and_sync)
        worker.signals.viewUpdateStarted.connect(self.jobView.viewUpdateStarted)
        worker.signals.progress.connect(self.jobView.writeLog)
        worker.signals.viewUpdateFinished.connect(self.jobView.viewUpdateFinished)

        # Execute job
        self.threadpool.start(worker)

    # Setup the SSH connection on a separate thread to
    # keep the app responsive
    def __connect(self, worker, *args, **kwargs):

        # Write and emit connection startup to log
        worker.signals.progress.emit({"connectionID": self.connectionID,
                                      "jobID": None,
                                      "message": "Connecting with %s" % self.connectionName,
                                      "messageType": "INFO"})

        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        try:
            with open(user_config_file) as f:
                ssh_config.parse(f)
        except:
            worker.signals.progress.emit({"connectionID": self.connectionID,
                                           "jobID": None,
                                           "message": "Could not parse ~/.ssh/config, does the file exist?",
                                           "messageType": "ERROR"})
            return False

        try:
            config = ssh_config.lookup(self.hostName)
            proxy = paramiko.ProxyCommand(config['proxycommand'])
            assert config['hostname']
            assert config['user']
        except:
            worker.signals.progress.emit({"connectionID": self.connectionID,
                                          "jobID": None,
                                          "message": "The host configuration does not have a hostname, username or proxy command.",
                                          "messageType": "ERROR"})
        try:
            self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sshClient.load_system_host_keys()
            self.sshClient.connect(config['hostname'], username=config['user'], sock=proxy)
            self.sshClient.get_transport().set_keepalive(15)
            self.sftpClient = self.sshClient.open_sftp()
        except SSHException as err:
            worker.signals.progress.emit({"connectionID": self.connectionID,
                                          "jobID": None,
                                          "message": "SSH connection failed with error: %s" % str(err),
                                          "messageType": "ERROR"})
        except:
            worker.signals.progress.emit({"connectionID": self.connectionID,
                                          "jobID": None,
                                          "message": "Connection error:: %s" % str(sys.exc_info()[1]),
                                          "messageType": "ERROR"})

        if self.isConnected():
            worker.signals.progress.emit({"connectionID": self.connectionID,
                                          "jobID": None,
                                          "message": "Connection established",
                                          "messageType": "SUCCESS"})
            return True

        return False


    def syncJobs(self):

        # For very fast synchronization times, the view might not exist yet,
        # causing a crash. Therefore, check if the view has been set
        if hasattr(self, "jobView"):
            worker = Worker(self.__sync)
            worker.signals.viewUpdateStarted.connect(self.jobView.viewUpdateStarted)
            worker.signals.progress.connect(self.jobView.writeLog)
            worker.signals.viewUpdateFinished.connect(self.jobView.viewUpdateFinished)

            # Execute job
            self.threadpool.start(worker)

    def __sync(self, worker, *args, **kwargs):
        worker.signals.progress.emit({"connectionID": self.connectionID,
                                      "jobID": None,
                                      "message": "Syncing jobs with server...",
                                      "messageType": "INFO"})
        jobXML = self.exec_cmd('qstat -r -xml')
        root = ET.fromstring(jobXML)

        # Clear table
        self.tblJobs.remove(where('connectionID') == self.connectionID)


        # Insert pending/running jobs
        n_jobs = 0
        for queue in root:
            for job in queue.findall("job_list"):

                jobDetails = job.find("full_job_name").text.split(config.JOB_SEPARATOR)
                if jobDetails[0] != config.JOB_PREFIX:
                    continue

                jobName = jobDetails[1].replace("_", " ")
                projectFolder = jobDetails[2]
                singularityImg = jobDetails[3]
                editor = jobDetails[4]
                port = jobDetails[5]

                jobID = int(job.find("JB_job_number").text)
                nCPU = int(job.find("slots").text)
                status = job.find("state").text

                workerNode = None
                startTime = None

                if status == "qw":
                    status = 0
                    startTime = job.find("JB_submission_time").text.replace("T", " ")
                elif status == 'r':
                    status = 1
                    startIndex = int(job.find("queue_name").text.find("@")) + 1
                    endIndex = int(job.find("queue_name").text.find(".compute.hpc"))
                    workerNode = job.find("queue_name").text[startIndex:endIndex]
                    startTime = job.find("JAT_start_time").text.replace("T", " ")
                elif status == "dr":
                    continue # do not sync jobs that are marked for deletion
                else:
                    status = -1

                for resource in job.findall("hard_request"):
                    if resource.get("name") == "h_rt":
                        runTime = math.floor(int(resource.text) / 3600)

                    elif resource.get("name") == "h_vmem":
                        memory = resource.text


                # Update jobID or insert them if they are not in the DB
                # (e.g. if they were submitted from another PC)
                self.tblJobs.upsert({'connectionID': self.connectionID,
                             "jobID": jobID,
                             'projectFolder': projectFolder,
                             'jobName': jobName,
                             'runTime': runTime,
                             'startTime': startTime,
                             'status': status,
                             "nCPU": nCPU,
                             'nGPU': 0,
                             'memory': memory,
                             'workerNode': workerNode,
                             'port': port,
                             'editor': editor,
                             'singularityImg': singularityImg}, (where('connectionID') == self.connectionID) & (where('jobID') == jobID))
                n_jobs+=1

        self.getJobsFromDB()

        worker.signals.progress.emit({"connectionID": self.connectionID,
                                      "jobID": None,
                                      "message": "Synchronization successful, %d jobs were found" % n_jobs,
                                      "messageType": "SUCCESS"})


    #  projectFolder, singularityImg, jobName, runTime, nCPU, nGPU, memory, editor
    def submitToQueue(self, job, jobview):

        worker = Worker(self.__submit, job)
        worker.signals.viewUpdateStarted.connect(jobview.viewUpdateStarted)
        worker.signals.progress.connect(self.jobView.writeLog)
        worker.signals.result.connect(self.saveJobToDB)
        worker.signals.viewUpdateFinished.connect(jobview.viewUpdateFinished)

        self.threadpool.start(worker)


    def __submit(self,  worker, job):

        worker.signals.progress.emit({'connectionID': self.connectionID,
                                      'jobID': job.jobID,
                                      "message": "Submitting job %s ... " % job.jobName,
                                      "messageType": "INFO"})

        fullJobName = job.jobName
        fullJobName = fullJobName.replace(" ", "_")
        job.port = randint(8787, 10000)

        fullJobName = "%s%s%s%s%s%s%s%s%s%s%d" % (config.JOB_PREFIX, config.JOB_SEPARATOR,
                                                       fullJobName,  config.JOB_SEPARATOR,
                                                       job.projectFolder,  config.JOB_SEPARATOR,
                                                       job.singularityImg,  config.JOB_SEPARATOR,
                                                       job.editor,  config.JOB_SEPARATOR,
                                                       job.port)

        projectPath = self.projectRootFolder + "/" + job.projectFolder
        cookiesPath = projectPath + "/cookies"
        singularityPath = self.singularityFolder + "/" + job.singularityImg

        # SGE specific
        if job.nCPU > 1:
            threads = "-pe threaded %d" % job.nCPU
        else:
            threads = ""

        if job.editor == "Rserver":
            cmd = "cd %s; qsub -b yes -cwd -N %s -l h_rt=%s:00:00 -l h_vmem=%sG %s \"singularity run --app rserver %s --www-port=%d --auth-minimum-user-id=100 --server-set-umask=0\"" \
                  % (projectPath, fullJobName, job.runTime, job.memory, threads, singularityPath, job.port)
        else:
            cmd = "cd %s; qsub -b yes -cwd -N %s -l h_rt=%s:00:00 -l h_vmem=%sG %s \"singularity run --app jupyterlab %s --ip 0.0.0.0 --port %d --no-browser \"" \
                  % (projectPath, fullJobName, job.runTime, job.memory, threads, singularityPath, job.port)


        jobOutput = self.exec_cmd(cmd)
        jobNumberPattern = re.compile("Your job (\d+) ")
        job.jobID = int(jobNumberPattern.search(jobOutput).group(1))

        worker.signals.progress.emit({'connectionID': self.connectionID,
                                      'jobID': job.jobID,
                                      "message": "Job <b>%d</b> submitted with command: <i>%s</i>" % (job.jobID, cmd),
                                      "messageType": "SUCCESS"})

        return job


    def save(self):

        print("calling save in connections.py")
        if self.connectionID:
            self.tblConnections.update({'hostName': self.hostName,
                                 'connectionName': self.connectionName,
                                 'passphrase': self.passphrase,
                                 'gridEngine': self.gridEngine,
                                 'projectRootFolder': self.projectRootFolder,
                                 'singularityFolder': self.singularityFolder}, where('connectionID') == self.connectionID)
        else:
            connectionID = self.tblConnections.insert({'hostName': self.hostName,
                                 'connectionName': self.connectionName,
                                 'passphrase': self.passphrase,
                                 'gridEngine': self.gridEngine,
                                 'projectRootFolder': self.projectRootFolder,
                                 'singularityFolder': self.singularityFolder})

            # Sort of mysql_insert_id
            self.tblConnections.update({'connectionID': connectionID}, doc_ids=[connectionID])
            self.connectionID = connectionID
            return self


    # Check whether the sshClient is connected and active
    def isConnected(self):

        if self.sshClient.get_transport():
            return self.sshClient.get_transport().is_active()

        return False


    # Private get function
    def __get(self):
        conn = self.tblConnections.search(where('connectionID') == self.connectionID)[0]

        self.hostName = conn['hostName']
        self.connectionName = conn['connectionName']
        self.passphrase = conn['passphrase']
        self.gridEngine = conn['gridEngine']
        self.projectRootFolder = conn['projectRootFolder']
        self.singularityFolder = conn['singularityFolder']

    def getProjects(self):
        if self.file_exists(self.projectRootFolder):

            projects = []
            for file in self.sftpClient.listdir(self.projectRootFolder):
                fileattr = self.sftpClient.lstat("%s/%s" % (self.projectRootFolder, file))
                if stat.S_ISDIR(fileattr.st_mode):
                    projects.append(file)

            projects.sort()
            return projects

        #logger = Logger(connectionID=self.connectionID)
        #logger.writeLine(message="Project root folder %s not found. Please edit connection and make sure the root folder exists" % self.projectRootFolder, messageType="error")
        return False

    def getSingularityImages(self):
        if self.file_exists(self.singularityFolder):
            images = []

            for file in self.sftpClient.listdir(self.singularityFolder):
                fileattr = self.sftpClient.lstat("%s/%s" % (self.singularityFolder, file))
                if stat.S_ISREG(fileattr.st_mode) and os.path.splitext(file)[1] == ".sif":
                    images.append(file)

            images.sort()
            return images

        return False

    def getEditors(self):
        return ["Rserver", "Jupyterlab"]

    @staticmethod
    def getAll():
        connections = config.DB.table("connections").all()
        return sorted(connections, key=lambda i: i['connectionName'], reverse=False)

    def file_exists(self, file_or_folder="/hpc/pmc_stunnenberg/wout"):
        try:
            if self.isConnected():
                if self.sftpClient.stat(file_or_folder):
                    return True
            else:
                return False
        except SFTPError as e:
            # Print error to the log
            return False
        except OSError:
            return False


    # def get_remote_files(self, path):
    #     pass

    def exec_cmd(self, command):
        try:
            (stdin, stdout, stderr) = self.sshClient.exec_command(command)
        except:
            print('SSH PROBLEMS')
            return False

        return "".join(stdout.readlines())



##########################################################
#############          DELEGATES             #############
##########################################################

class ProgressDelegate(QStyledItemDelegate):

    def __init__(self, view):
        super().__init__(view)

    def paint(self, painter, option, index):

        jobIDs = list(index.model().jobs.keys())
        status = getattr(index.model().jobs[jobIDs[index.row()]], "status")
        #status = .jobs[index.row()]["status"]
        if status != 1:
            return

        # startTime = index.model().jobs[index.row()]["startTime"]
        startTime = getattr(index.model().jobs[jobIDs[index.row()]], "startTime")

        # if the job did not start yet, there is not progress to show
        if startTime:
            time_elapsed = datetime.now() - datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
            #runtime = index.model().jobs[index.row()]["runTime"]
            runTime = getattr(index.model().jobs[jobIDs[index.row()]], "runTime")

            min_left = int(runTime) * 60 - time_elapsed.total_seconds() / 60

            progress = time_elapsed.total_seconds() / (int(runTime) * 3600) * 100

            opt = QStyleOptionProgressBar()
            opt.rect = option.rect
            opt.minimum = 0
            opt.maximum = 100
            opt.progress = 100 - progress
            opt.text = "%d min (%d%%)" % (min_left, round(100-progress))
            opt.textVisible = True

            if min_left <= config.MINUTES_LEFT_WHEN_WARNING_PROGRESS:
                pal = opt.palette
                col = QColor(255, 0, 0)
                pal.setColor(QPalette.Highlight, col)
                opt.palette = pal

            QApplication.style().drawControl(QStyle.CE_ProgressBar, opt, painter)
