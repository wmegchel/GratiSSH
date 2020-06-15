# About GratiSSH
The _GRAphical Tool for Interactive Scientfic Scripting on HPC (GratiSSH)_ makes it easy to run an interactive Rstudio server or JupyterLab environment on a remote Linux server. GratiSSH was designed to work with HPCs that run the popular [SLURM](https://slurm.schedmd.com/documentation.html) or [SGE](https://en.wikipedia.org/wiki/Oracle_Grid_Engine) workload managers.

GratiSSH is written in Python and uses the PyQt5 graphical environment. Under the hood, GratiSSH connects to a [singularity container](https://sylabs.io/docs/) that is stored on the remote server. This singularity container contains [Rstudio server](https://rstudio.com/products/rstudio/#rstudio-server), [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/) and many R-packages tailored to single cell analysis, such as [Seurat](https://satijalab.org/seurat/) and [Monocle3](https://cole-trapnell-lab.github.io/monocle3). 

GratiSSH is designed to manage multiple jobs on one or multiple remote servers in parallel. Pre-combined binaries for Mac OSX and Ubuntu are available under "releases". 

__Of note__, future releases of GratiSSH will also manages "jobs" on a localhost, or remote server without a workload manager. 

# Setting up your SSH config
GratiSSH uses the connections defined in `~/.ssh/config`. 

## Configuring singularity
By default, singularity binds your _home directory_ and _current working directory_. This means that you cannot access files in other folders. This can by changed by setting the __SINGULARITY_BIND__ variable in your `~/.bashrc` file. 

# Getting GratiSSH
## Downloading the latest release build
- Download the [latest release](https://github.com/wmegchel/GratiSSH/releases) under 'assets';
- Unzip the program
- Double click the unzipped program to start

# Working with GratiSSH
## Adding/Editing a connection
First we need to add a new connection. 

* Click `connection` -> `Add connection`

![Adding a connection](img/01_edit_connection.png)

A new window is shown where you can define the preferences for your new job.

* Select the `host name` you want to connect to from the dropdown menu. These host names are taken from the `~/.ssh/config` file. If your host is not in this menu, add it to the  `~/.ssh/config` file;
* Provide a `connection name`, this can be any name;
* Provide the `passphrase` you defined for your ssh key. If you did not provide any key, leave this field blank;
* Choose `grid engine` `SGE` or `SLURM`.
* Set the path to the singularity files. 
* Set the folder where your projects are stored.
* Click `save`.

![The connection dialog](img/02_edit_connection_dialog.png)

### Connecting with the HPC host
Now that our connection is ready, we can to connect to the host. 

* Click `connection` -> `your connection name` -> `connect`
* If the connection is OK, the program will connect to the server and synchronize your jobs;

![The job list](img/03_job_list.png)

### Adding a new job
To submit a new job: 

* Click `add job`;
* Select the project you want to work on. These are the subfolders defined in the project folder you selected above.
* Type a suitable job name;
* Select the `runtime`, `number of CPUs` and `memory` required for your job;
* Select the `singularity image` you want to use for the job;
* Select `RServer` as the editor; 
* Click `OK`.

![Adding a new job](img/04_add_job.png)

The job will be added to the list with a "stopwatch" symbol, indicating that it is scheduled, but not yet running. This status will be updated automatically every 10 mins, but we can do this manually using the `sync jobs` button. 

* Click the `sync jobs` button every 20s until the job status changes. If the job is running a blue bar with remaining compute time will be shown;

![Scheduled and active jobs](img/05_job_scheduled.png)

* When the job is running, right click on your job and select `Open job in browser window`
* A new tab will open in your browser with `Rserver`.
* You can delete a job by right clicking the job and seelcting `Delete job`;
* You can delete all running jobs by clicking the `Delete all jobs` button;

__NB: Jobs will keep running when you close GratiSSH, make sure you delete running jobs that are not needed any more, because compute time will be deduced from our budget.__ You can close the program and re-attach running jobs after re-opening `GratiSSH` with the `sync jobs` button. Jobs that were not started from `GratiSSH`, e.g. a mapping job, will not be opened in this program.

![Starting RServer from a running job](img/06_open_running_job.png)

## Configuring JupyterLab
If you prefer to work in *JupyterLab*, you need to configure a security password first. The simplest way of doing this is running JupyterLab from the singularity image. Since singularity is only installed on the compute nodes and not on the submission nodes, we need to connect to a compute node first. Follow these steps:

* Open a terminal and connect to the HPC;
* Type `qlogin -l h_rt=2:00:00 -l h_vmem=8.0G` and provide your password. 
* Now you should be on a compute node, indicated by a terminal prompt with <your_username>@n00XXX;
* Type: `singularity exec /hpc/pmc_stunnenberg/shared/singularity_images/SC_container_Apr25.sif jupyter notebook password`, this may take a few seconds;
* Provide your Jupyter password, this will be hashed and stored in `~/.jupyter/jupyter_notebook_config.json`;
* Now you can start a new job and select `JupyterLab` as your preferred editor. When you open the job in a browser window, you will be prompted for the password you just set.

# Running R-scripts in batch mode
Using the singularity container, you can also run R-scripts in batch mode. This is both convenient and good practice, because you are using the exact same environment with the same R-packages and versions that you use for the interactive jobs defined above. As an example, we will run an R-script that normalizes some Celseq2 data and plots a TSNE, UMAP and a small heatmap with cluster marker genes stored into PDF files.

* Open a terminal
```{r, eval = F, echo = T}
# Connect to HPC
ssh hpc

# Get the example files
wget https://raw.githubusercontent.com/wmegchel/GratiSSH/master/examples/example_TSNE_UMAP_Heatmap.R
wget https://github.com/wmegchel/GratiSSH/blob/master/examples/scRNAseq_Zic3_WT_and_KO.Rds

# Execute the R-script
singularity exec ~/ownCloud/sing_test/SC_container_Apr25.sif Rscript example_TSNE_UMAP_Heatmap.R
```

# Using singularity and Rstudio or JupterLab on your Macbook
Having established an Rstudio environment that works interactively and in batch mode on the HPC, we would like to use the same environment on our Macbook as well. This is possible and highly recommended. First, we need to install singularity.

* Activate the `30 min admin` in the self serivce app;
* Download singularity desktop at: `https://sylabs.io/singularity-desktop-macos/` and follow the installation instructions;
* If installation is finished, open a termimal and type `singularity`. If all went well, a list with options should appear.
* Copy the singularity image from the hpc: `scp hpc:/hpc/pmc_stunnenberg/shared/singularity_images/SC_container_Apr25.sif .`
* For Rstudio, type `singularity run --nv --app rstudio SC_container_Apr25.sif`
* For JupterLab, type `singularity run --nv --app jupyterlab SC_container_Apr25.sif`

# Listing the applications in a singularity container
`singularity inspect --list-apps SC_container_Apr25.sif`




## Building GratiSSH from source
todo
<!-- - Clone the Github repository -->
<!-- - Python3 -->
<!-- - PyQt5 -->
<!-- - tinydb -->
<!-- - paramiko -->
<!-- - @todo: how to install using pip3 or conda -->
