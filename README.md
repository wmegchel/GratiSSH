# GratiSSH
## About GratiSSH
The _GRAphical Tool for Interactive Scientfic Scripting on HPC (GratiSSH)_ makes it easy to run an interactive Rstudio server or JupyterLab environment on a remote Linux server. GratiSSH was designed to work with HPCs that run the popular [SLURM](https://slurm.schedmd.com/documentation.html) or [SGE](https://en.wikipedia.org/wiki/Oracle_Grid_Engine) workload managers.

GratiSSH is written in Python and uses the PyQt5 graphical environment. Under the hood, GratiSSH connects to a [singularity container](https://sylabs.io/docs/) that is stored on the remote server. This singularity container contains [Rstudio server](https://rstudio.com/products/rstudio/#rstudio-server), [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/) and many R-packages tailored to single cell analysis, such as [Seurat](https://satijalab.org/seurat/) and [Monocle3](https://cole-trapnell-lab.github.io/monocle3). 

GratiSSH is designed to manage multiple jobs on one or multiple remote servers in parallel. Pre-combined binaries for Mac OSX and Ubuntu are available under "releases". 

__Of note__, future releases of GratiSSH will also manages "jobs" on a localhost, or remote server without a workload manager. 

## Configuration
### SSH host configuration file
GratiSSH uses the connections defined in `~/.ssh/config`. Before you download GratiSSH, make sure you at least one host is defined here. See examples/example_ssh_config. Create an RSA key pair for your host using **ssh-keygen** and send the public key to the host using **ssh-copy-id**

```{bash, eval=F}
ssh-keygen -f ~/.ssh/my_hpc_rsa_key
ssh-copy-id -i ~/.ssh/my_hpc_rsa_key my_username@host
```
### Configuring singularity
By default, singularity binds your _home directory_ and _current working directory_. This means that you cannot access files in other folders on the remote server. This can by changed by setting the __SINGULARITY_BIND__ variable in your `~/.bashrc` file. For example:

```{bash, eval=F}
export SINGULARITY_BIND="/home/research/,/scratch/wout"
```
binds the `/home/research` and `/scratch/wout` directories as well, which become available in your singularity container.

## Downloading the latest release build
- Download the [latest release](https://github.com/wmegchel/GratiSSH/releases) under 'assets';
- Unzip the program
- Double click the unzipped program to start

## Working with GratiSSH
### Adding/Editing a connection
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
* Select the `project` you want to work on. These are the subfolders defined in the project folder you selected above.
* Provide the `job name`;
* Select the `runtime`, `number of CPUs` and `memory` required for your job;
* Select the `singularity image` you want to use for the job;
* Select `RServer` as the editor; 
* Click `OK`.

![Adding a new job](img/04_add_job.png)

The job will be added to the list with a "stopwatch" symbol, indicating that it is scheduled, but not yet running. This status will be updated automatically every 10 mins, but we can do this manually using the `sync jobs` button. 

* Click the `sync jobs` with small intervals (say 5 or 10 seconds) until the job status changes. A blue timer bar shows the remaining run time when the job is running.

![Scheduled and active jobs](img/05_job_scheduled.png)

* When the job is running, right click on your job and select `Open job in browser window`
* A new tab will open in your browser with `Rserver`.
* Sometimes, Rserver or Jupyterlab is not fully loaded yet. In this case, it may help to reload the browser window (a few times).
* Delete a job by right clicking the job and selecting `Delete job`;
* Delete all running jobs by clicking the `Delete all jobs` button;

__NB: Jobs will keep running when you close GratiSSH, make sure you delete running jobs that are not needed any more, because compute time will be deduced from our budget.__ You can close the program and re-attach running jobs after re-opening `GratiSSH` with the `sync jobs` button. Jobs that were not started from `GratiSSH`, e.g. a mapping job, will not be opened in this program.

![Starting RServer from a running job](img/06_open_running_job.png)

### Configuring JupyterLab
If you prefer to work in *JupyterLab*, you need to configure a security password first. The simplest way of doing this is running JupyterLab from the singularity image:

```{bash}
singularity exec container_name.sif jupyter notebook password
```
Within a few seconds, you will be promped for a new password. The hashed password will be stored in `~/.jupyter/jupyter_notebook_config.json`.  Now start a new job and select `JupyterLab` as your preferred editor. When you open the job in a browser window, you will be prompted for the password you just set.

## Running R-scripts in batch mode
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

## Building GratiSSH from source
To build GratiSSH from source, you need **python3** and the python packages: pyinstaller, PyQt5, paramiko, tinydb, sshconf, sshtunnel and waitingspinnerwidget. 


```{bash}
pip3 install pyinstaller
pip3 install PyQt5
pip3 install paramiko
pip3 install tinydb
pip3 install sshconf
pip3 install sshtunnel
pip3 install pyqtspinner
```

Clone the git repository and run pyinstaller:
```{bash}
pyinstaller --onefile gratissh_custom.spec
```

