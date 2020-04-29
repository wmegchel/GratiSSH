import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError, HandlerSSHTunnelForwarderError

# JobModel loaded into the TableView
class Job(QWidget):

    msgSignal = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args)
        self.connection = kwargs['connection']
        self.jobID = kwargs['jobID']
        self.jobName = kwargs['jobName']
        self.projectFolder = kwargs['projectFolder']
        self.startTime = kwargs['startTime']
        self.runTime = kwargs['runTime']
        self.nCPU = kwargs['nCPU']
        self.nGPU = kwargs['nGPU']
        self.memory = kwargs['memory']
        self.singularityImg = kwargs['singularityImg']
        self.workerNode = kwargs['workerNode']
        self.status = kwargs['status']
        self.editor = kwargs['editor']
        self.port = kwargs['port']
        self.tunnel = None

    def openSSHTunnel(self, jobView):

        self.msgSignal.connect(jobView.writeLog)

        user_config_file = os.path.expanduser("~/.ssh/config")
        try:
            if self.connection.passphrase != "":
                self.tunnel = SSHTunnelForwarder(self.connection.hostName, ssh_config_file=user_config_file,
                                                             remote_bind_address=(self.workerNode, int(self.port)),
                                                             local_bind_address=('localhost', int(self.port)),
                                                             allow_agent=True, ssh_password=self.connection.passphrase,
                                                             set_keepalive=10)
            else:
                self.tunnel = SSHTunnelForwarder(self.connection.hostName, ssh_config_file=user_config_file,
                                                 remote_bind_address=(self.workerNode, int(self.port)),
                                                 local_bind_address=('localhost', int(self.port)),
                                                 allow_agent=True,
                                                 set_keepalive=10)

            self.tunnel.start()

        except BaseSSHTunnelForwarderError as e:
            self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                 "jobID": self.jobID,
                                 "message": "SSH tunnel error:: %s" % str(e),
                                 "messageType": "ERROR"})
        except HandlerSSHTunnelForwarderError as e:
            self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                 "jobID": self.jobID,
                                 "message": "SSH tunnel error:: %s" % str(e),
                                 "messageType": "ERROR"})
        except:
            self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                 "jobID": self.jobID,
                                 "message": "SSH tunnel error:: %s" % str(sys.exc_info()[1]),
                                 "messageType": "ERROR"})

    def closeSSHTunnel(self, jobView):

        self.msgSignal.connect(jobView.writeLog)

        if isinstance(self.tunnel, SSHTunnelForwarder):
            try:
                # 1. stop the tunnel
                self.tunnel.close()
            except BaseSSHTunnelForwarderError as e:
                self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                              "jobID": self.jobID,
                                              "message": "SSH tunnel error:: %s" % str(e),
                                              "messageType": "ERROR"})
            except HandlerSSHTunnelForwarderError as e:
                self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                     "jobID": self.jobID,
                                     "message": "SSH tunnel error:: %s" % str(e),
                                     "messageType": "ERROR"})

            except:
                self.msgSignal.emit({"connectionID": self.connection.connectionID,
                                     "jobID": self.jobID,
                                     "message": "SSH tunnel error:: %s" % str(sys.exc_info()[1]),
                                     "messageType": "ERROR"})