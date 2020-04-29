import os
from tinydb import TinyDB, Query, where

DB = TinyDB(os.path.expanduser('~/HPC_jobs.json'))

JOB_PREFIX = "IJM"
JOB_SEPARATOR = "__"
WINDOW_TITLE = "HPC interactive job manager"
#MAIN_WINDOW_SIZE = [2100, 1500]

# Perform qstat every 5 mins
SYNC_JOBS_WITH_SERVER_INTERVAL_SECONDS = 5*60

# Change the progress bar from blue to red if time left is less or equal to this setting
MINUTES_LEFT_WHEN_WARNING_PROGRESS = 10

# Form selection and validation options
JOB_MIN_RUNTIME_HOURS = 1
JOB_MAX_RUNTIME_HOURS = 96

JOB_MIN_AMOUNT_OF_CPU = 1
JOB_MAX_AMOUNT_OF_CPU = 48

JOB_MIN_AMOUNT_OF_MEMORY_GB = 1
JOB_MAX_AMOUNT_OF_MEMORY_GB = 256

JOB_MIN_AMOUNT_OF_GPU = 0
JOB_MAX_AMOUNT_OF_GPU = 0

SHOW_DEBUG_INFO = False