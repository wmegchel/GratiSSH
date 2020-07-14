
from sshtunnel import *
import os
import config

class Job:

    def __init__(self, connection=None, jobID=None, jobName=None, projectFolder=None, startTime=None,
                 runTime=config.JOB_DEFAULT_RUNTIME_HOURS, nCPU=config.JOB_DEFAULT_AMOUNT_OF_CPU,
                 nGPU=config.JOB_DEFAULT_AMOUNT_GPU, memory=config.JOB_DEFAULT_AMOUNT_OF_MEMORY_GB,
                 singularityImg=None, workerNode=None, status=None, editor=None, port=None, tunnel=None):

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

    def openSSHTunnel(self, jobView):

        user_config_file = os.path.expanduser("~/.ssh/config")

        try:
            if isinstance(self.tunnel, SSHTunnelForwarder) and self.tunnel.is_alive:
                return True

            if self.connection.passphrase == "":
                passphrase = None
            else:
                passphrase = self.connection.passphrase

            self.tunnel = SSHTunnelForwarder(ssh_address_or_host=self.connection.hostName,
                                             ssh_private_key_password=passphrase,
                                             ssh_config_file=user_config_file,
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
