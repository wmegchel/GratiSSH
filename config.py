import os
from tinydb import TinyDB, Query, where

DB = TinyDB(os.path.expanduser('~/HPC_jobs.json'))

JOB_PREFIX = "IJM"
JOB_SEPARATOR = "__"
WINDOW_TITLE = "GratiSSH"
#MAIN_WINDOW_SIZE = [2100, 1500]


# sync with server every 10 seconds when there are pending jobs
SYNC_JOBS_WITH_SERVER_INTERVAL_SECONDS_SHORT = 10

# sync with server every 5 min when there are no pending jobs (all running)
SYNC_JOBS_WITH_SERVER_INTERVAL_SECONDS_LONG = 5 * 60

# Change the progress bar from blue to red if time left is less or equal to this setting
MINUTES_LEFT_WHEN_WARNING_PROGRESS = 15

# Form selection and validation options
JOB_MIN_RUNTIME_HOURS = 1
JOB_MAX_RUNTIME_HOURS = 96
JOB_DEFAULT_RUNTIME_HOURS = 2

JOB_MIN_AMOUNT_OF_CPU = 1
JOB_MAX_AMOUNT_OF_CPU = 48
JOB_DEFAULT_AMOUNT_OF_CPU = 1

JOB_MIN_AMOUNT_OF_MEMORY_GB = 8.0
JOB_MAX_AMOUNT_OF_MEMORY_GB = 1024.0
JOB_DEFAULT_AMOUNT_OF_MEMORY_GB = 60.0

JOB_MIN_AMOUNT_OF_GPU = 0
JOB_MAX_AMOUNT_OF_GPU = 0
JOB_DEFAULT_AMOUNT_GPU = 0

SHOW_DEBUG_INFO = False