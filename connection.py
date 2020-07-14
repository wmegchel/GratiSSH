import config
from tinydb import TinyDB, Query, where
import paramiko
from paramiko import SFTPError, SSHException
from PyQt5.QtCore import *

import os, sys
import stat


class Connection:

    def __init__(self, connectionID=None, connectionName=None, hostName=None, passphrase=None,
                 gridEngine=None, singularityFolder=None, projectRootFolder=None,
                 threadpool=QThreadPool(), sshClient=paramiko.SSHClient(), sftpClient=None):
        super(Connection, self).__init__()

        self.tblConnections = config.DB.table('connections')

        # Fields
        self.connectionID = connectionID
        self.connectionName = connectionName
        self.hostName = hostName
        self.passphrase = passphrase
        self.gridEngine = gridEngine
        self.singularityFolder = singularityFolder
        self.projectRootFolder = projectRootFolder
        self.threadpool = threadpool
        self.sshClient = sshClient
        self.sftpClient = sftpClient


    # Setup the SSH connection on a separate thread to keep the app responsive
    def connect(self, worker, *args, **kwargs):

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

        # Check whether the sshClient is connected and active

    def isConnected(self):
        if self.sshClient.get_transport():
            return self.sshClient.get_transport().is_active()

        return False

    def disconnect(self):
        self.sshClient.close()




    ################


    def delete(self):
        self.tblConnections.remove(where('connectionID') == self.connectionID)


    def save(self):

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


    @staticmethod
    def getByID(connectionID):
        conn = config.DB.table("connections").search(where('connectionID') == connectionID)[0]
        conn = Connection(connectionID=conn["connectionID"],
                          connectionName=conn["connectionName"],
                          hostName=conn["hostName"],
                          passphrase=conn["passphrase"],
                          gridEngine=conn["gridEngine"],
                          singularityFolder=conn["singularityFolder"],
                          projectRootFolder=conn["projectRootFolder"])

        return conn

    @staticmethod
    # Returns a dictionary of connection objects, sorted by connectionName
    def getAll():
        connections = config.DB.table("connections").all()
        sorted_connections = sorted(connections, key=lambda i: i['connectionName'], reverse=False)
        connections = {}
        for conn in sorted_connections:
            foo = Connection.getByID(conn['connectionID'])
            connections[conn['connectionID']] = foo

        return connections


    def exec_cmd(self, command):
        try:
            (stdin, stdout, stderr) = self.sshClient.exec_command(command)
        except:
            print('SSH PROBLEMS')
            return False

        return "".join(stdout.readlines())