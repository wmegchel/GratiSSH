from abc import ABC, abstractmethod

class JobQueue(ABC):


    def __init__(self, connection):
        super(JobQueue, self).__init__()
        self.connection = connection

    @staticmethod
    def getQueueObject(connection):
        if connection.gridEngine == "SGE":
            from sge_queue import SgeQueue
            return SgeQueue(connection)
        else:
            from slurm_queue import SlurmQueue
            return SlurmQueue(connection)

    @abstractmethod
    def syncJobs(self, worker):
        pass

    @abstractmethod
    def submitJob(self):
        pass

    @abstractmethod
    def deleteJob(self):
        pass




