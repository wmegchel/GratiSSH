# ssh worker here
from job import Job
from PyQt5.QtCore import *
import sys


class WorkerSignals(QObject):

    # worker signals that are sent on job submission, job synchronization
    # (e.g. qstat or squeue) and job deletion

    # update started: disable buttons and start progress spinner
    updateStarted = pyqtSignal()

    # update finished: enable buttons and stop progress spinner
    updateFinished = pyqtSignal()

    # return log message that will be displayed in the joblist.logEdit
    progress = pyqtSignal(dict)

    # return exception
    error = pyqtSignal(tuple)

    # return Job object of submitted job
    jobSubmitted = pyqtSignal(Job)

    # return dictionary of jobs that are synchronized
    jobsSynced = pyqtSignal(dict)

    # return jobID of deleted job
    jobDeleted = pyqtSignal(int)



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
            self.signals.updateStarted.emit()
            result = self.fn(self, *self.args, **self.kwargs)
        except:

            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value))
        else:
            if self.kwargs['task'] == "submit":
                self.signals.jobSubmitted.emit(result)
            elif self.kwargs['task'] == "sync":
                self.signals.jobsSynced.emit(result)
            elif self.kwargs['task'] == "delete":
                self.signals.jobDeleted.emit(result)
            else:
                raise Exception("Unknown task")

        finally:
            self.signals.updateFinished.emit()  # Done
