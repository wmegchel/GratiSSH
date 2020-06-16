
from sshtunnel import *
from PyQt5.QtCore import *
import os


class Job:

    #msgSignal = pyqtSignal(dict)

    def __init__(self, connection=None, jobID=None, jobName=None, projectFolder=None, startTime=None,
                 runTime=2, nCPU=1, nGPU=0, memory=16, singularityImg=None,
                 workerNode=None, status=None, editor=None, port=None, tunnel=None):

        # super(Job, self).__init__()
        # print("init super done")
        self.connection = connection
        self.jobID = jobID
        self.jobName = jobName
        self.projectFolder = projectFolder
        self.startTime = startTime
        self.runTime = runTime
        self.nCPU = nCPU
        self.nGPU = nGPU
        self.memory = memory
        self.singularityImg = singularityImg
        self.workerNode = workerNode
        self.status = status
        self.editor = editor
        self.port = port
        self.tunnel = tunnel
        # print("all init done")

        #super(Job, self).__init__(jobID)

    def openSSHTunnel(self, jobView):

        user_config_file = os.path.expanduser("~/.ssh/config")

        try:
            if isinstance(self.tunnel, SSHTunnelForwarder) and self.tunnel.is_alive():
                return

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
            return True
        except BaseSSHTunnelForwarderError as e:
            return str(e),
        except HandlerSSHTunnelForwarderError as e:
            return str(e),
        except:
            return str(sys.exc_info()[1])


    def closeSSHTunnel(self, jobView):

        if isinstance(self.tunnel, SSHTunnelForwarder):
            try:
                self.tunnel.close()
                return True
            except BaseSSHTunnelForwarderError as e:
                return str(e),
            except HandlerSSHTunnelForwarderError as e:
                return str(e),
            except:
                return str(sys.exc_info()[1])
