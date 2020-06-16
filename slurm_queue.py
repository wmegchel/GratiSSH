import sys, re, os
import config
from math import floor
from job import Job
from random import randint
from job_queue import JobQueue
import paramiko
from datetime import datetime

class SlurmQueue(JobQueue):

    def __init__(self, connection):
        super(SlurmQueue, self).__init__(connection)


    def syncJobs(self, worker, *args, **kwargs):

        if not self.connection.isConnected():
            self.connection.connect(worker)

        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        try:
            with open(user_config_file) as f:
                ssh_config.parse(f)
        except:
            worker.signals.progress.emit({"connectionID": self.connection.connectionID,
                                          "jobID": None,
                                          "message": "Could not parse ~/.ssh/config, does the file exist?",
                                          "messageType": "ERROR"})
            return False


        worker.signals.progress.emit({"connectionID": self.connection.connectionID,
                                      "jobID": None,
                                      "message": "Syncing jobs with server...",
                                      "messageType": "INFO"})

        sshConfig = ssh_config.lookup(self.connection.hostName)
        #print('running ---> squeue -u %s -h -o \"%%A||%%j||%%c||%%l||%%m||%%V||%%t||%%S||%%N\"' % sshConfig['user'])

        slurmJobs = self.connection.exec_cmd('squeue -u %s -h -o \"%%A||%%j||%%c||%%l||%%m||%%V||%%t||%%S||%%N\"' % sshConfig['user'])
        #print("sjo what do we get??", type(slurmJobs), len(slurmJobs))
        #print(slurmJobs)
        # JOBID | NAME | MIN_CPUS | TIME_LIMIT | MIN_MEMORY | SUBMIT_TIME | ST | START_TIME | NODELIST
        # 1594774 | foobar |  1 | 1:00:00 | 5G | 2020-06-09T11: 16:53 | R | 2020-06-09T11: 16:54 | n0084

        # Insert pending/running jobs
        jobs = {}
        for slurmJob in slurmJobs.splitlines():

                fields = slurmJob.split("||")
                jobDetails = fields[1].split(config.JOB_SEPARATOR)
                if jobDetails[0] != config.JOB_PREFIX:
                    continue

                jobName = jobDetails[1].replace("_", " ")
                projectFolder = jobDetails[2]
                singularityImg = jobDetails[3]
                editor = jobDetails[4]
                port = jobDetails[5]

                jobID = int(fields[0])
                nCPU = int(fields[2])
                status = fields[6]

                workerNode = None
                startTime = None

                if fields[3].find("-") != -1:
                    runTime = int(datetime.strptime(fields[3], "%d-%H:%M:%S").strftime("%H")) * 24 + \
                              int(datetime.strptime(fields[3], "%d-%H:%M:%S").strftime("%H")) + \
                              int(datetime.strptime(fields[3], "%d-%H:%M:%S").strftime("%M")) / 60
                else:
                    runTime = int(datetime.strptime(fields[3], "%H:%M:%S").strftime("%H")) + \
                              int(datetime.strptime(fields[3], "%H:%M:%S").strftime("%M")) / 60

                memory = fields[4]

                if status == "PD":
                    status = 0
                    startTime = datetime.strptime(fields[5], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                elif status == 'R':
                    status = 1
                    startTime = datetime.strptime(fields[7], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    workerNode = fields[8]
                else:
                    continue

                jobs[jobID] = Job(connection=self.connection,
                                  jobID=jobID,
                                  jobName=jobName,
                                  projectFolder=projectFolder,
                                  startTime=startTime,
                                  runTime=runTime,
                                  nCPU=nCPU,
                                  nGPU=0,
                                  memory=memory,
                                  singularityImg=singularityImg,
                                  workerNode=workerNode,
                                  status=status,
                                  editor=editor,
                                  port=port)

        worker.signals.progress.emit({"connectionID": self.connection.connectionID,
                                      "jobID": None,
                                      "message": "Synchronization successful, %d jobs were found" % len(jobs),
                                      "messageType": "SUCCESS"})

        # the updated jobs will be signalled towards the slot jobTableModel:updateJobs
        return jobs



    def submitJob(self, worker, *args, **kwargs):

        job = kwargs['job']

        worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                      'jobID': job.jobID,
                                      "message": "Submitting job %s ... " % job.jobName,
                                      "messageType": "INFO"})

        fullJobName = job.jobName
        fullJobName = fullJobName.replace(" ", "_")
        job.port = randint(8787, 10000)

        fullJobName = "%s%s%s%s%s%s%s%s%s%s%d" % (config.JOB_PREFIX, config.JOB_SEPARATOR,
                                                  fullJobName, config.JOB_SEPARATOR,
                                                  job.projectFolder, config.JOB_SEPARATOR,
                                                  job.singularityImg, config.JOB_SEPARATOR,
                                                  job.editor, config.JOB_SEPARATOR,
                                                  job.port)

        projectPath = self.connection.projectRootFolder + "/" + job.projectFolder
#         cookiesPath = projectPath + "/cookies"
        singularityPath = self.connection.singularityFolder + "/" + job.singularityImg

        cmd = "sbatch --parsable -D %s --job-name=%s --time=%s:00:00 --mem=%dGB --nodes=1 --mincpus=%d --wrap" % (projectPath, fullJobName, job.runTime, job.memory, job.nCPU)

        if job.editor == "Rserver":
            cmd+= " \"singularity run --app rserver %s --www-port=%d --auth-minimum-user-id=100 --server-set-umask=0\"" % (singularityPath, job.port)
        else:
            cmd+= " \"singularity run --app jupyterlab %s --ip 0.0.0.0 --port %d --no-browser \"" % (singularityPath, job.port)

        job.jobID = int(self.connection.exec_cmd(cmd))

        worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                      'jobID': job.jobID,
                                      "message": "Job <b>%d</b> submitted with command: <i>%s</i>" % (
                                      job.jobID, cmd),
                                      "messageType": "SUCCESS"})

        #print("returning job now .. ")
        #print("jobID = %d" % job.jobID)
        return job


    def deleteJob(self, worker, *args, **kwargs):
        jobID = int(kwargs['jobID'])

        try:
            # send qdel command
            self.connection.exec_cmd("scancel %d" % jobID)

            # update log
            worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                          'jobID': jobID,
                                          'message': "Job %d deleted" % jobID,
                                          'messageType': 'SUCCESS'})
        except KeyError as e:
            worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                          'jobID': jobID,
                                          'message': str(e),
                                          'messageType': 'ERROR'})
        except:
            worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                          'jobID': jobID,
                                          'message': str(sys.exc_info()[1]),
                                          'messageType': 'ERROR'})

        return jobID


