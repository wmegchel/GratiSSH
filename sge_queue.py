import sys, re
import xml.etree.ElementTree as ET
import config
from math import floor
from job import Job
from job_queue import JobQueue


class SgeQueue(JobQueue):

    def __init__(self, connection):
        super(SgeQueue, self).__init__(connection)

    def syncJobs(self, worker, *args, **kwargs):

        if not self.connection.isConnected():
            self.connection.connect(worker)

        worker.signals.progress.emit({"connectionID": self.connection.connectionID,
                                      "jobID": None,
                                      "message": "Syncing jobs with server...",
                                      "messageType": "INFO"})
        jobXML = self.connection.exec_cmd('qstat -r -xml')
        root = ET.fromstring(jobXML)

        # Insert pending/running jobs
        jobs = {}
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
                        runTime = floor(int(resource.text) / 3600)

                    elif resource.get("name") == "h_vmem":
                        memory = float(resource.text[0:-1])

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

        job=kwargs['job']

        worker.signals.progress.emit({'connectionID': self.connection.connectionID,
                                      'jobID': job.jobID,
                                      "message": "Submitting job %s ... " % job.jobName,
                                      "messageType": "INFO"})

        fullJobName = job.jobName
        fullJobName = fullJobName.replace(" ", "_")
        fullJobName = "%s%s%s%s%s%s%s%s%s%s%d" % (config.JOB_PREFIX, config.JOB_SEPARATOR,
                                                  fullJobName, config.JOB_SEPARATOR,
                                                  job.projectFolder, config.JOB_SEPARATOR,
                                                  job.singularityImg, config.JOB_SEPARATOR,
                                                  job.editor, config.JOB_SEPARATOR,
                                                  job.port)

        projectPath = self.connection.projectRootFolder + "/" + job.projectFolder
        cookiesPath = projectPath + "/cookies"
        singularityPath = self.connection.singularityFolder + "/" + job.singularityImg

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

        jobOutput = self.connection.exec_cmd(cmd)
        jobNumberPattern = re.compile("Your job (\d+) ")
        job.jobID = int(jobNumberPattern.search(jobOutput).group(1))

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
            self.connection.exec_cmd("qdel %d" % jobID)

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
