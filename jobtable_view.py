from datetime import datetime
import config
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys, os


class JobTableView(QTableView):

    def __init__(self, jobTableModel):
        super(JobTableView, self).__init__()
        self.jobTableModel = jobTableModel
        self.dbTable = config.DB.table("jobs")


    def setView(self):
        self.setModel(self.jobTableModel)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.resizeHeaders()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        delegate = ProgressDelegate(self)
        self.setItemDelegateForColumn(11, delegate)

    def resizeHeaders(self):
        header = self.horizontalHeader()

        # Do not make the header bold when an item is selected
        header.setHighlightSections(False)

        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        # progress indicator takes rest of available space
        header.setSectionResizeMode(11, QHeaderView.Stretch)


    def context_menu(self):

        basedir = "icons"
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            basedir = os.path.join(sys._MEIPASS, "icons")

        menu = QMenu()
        add_job = menu.addAction("Add Job")
        add_job.setIcon(QIcon(os.path.join(basedir, "add_job_normal.png")))
        add_job.triggered.connect(lambda: self.parent().addJob())
        if self.selectedIndexes():
            jobID = list(self.jobTableModel.jobs.keys())[self.currentIndex().row()]

            view_job = menu.addAction("View job details")
            view_job.setIcon(QIcon(os.path.join(basedir, "view_job_32px_normal.png")))
            view_job.triggered.connect(lambda: self.parent().viewJob(jobID))

            delete_job = menu.addAction("Delete job")
            delete_job.setIcon(QIcon(os.path.join(basedir, "delete_jobs_normal.png")))
            delete_job.triggered.connect(lambda: self.parent().deleteJob(jobID))

            browse_job = menu.addAction("Open job in browser window")
            browse_job.setIcon(QIcon(os.path.join(basedir, "weblink_32px.png")))
            browse_job.triggered.connect(lambda: self.parent().browse(jobID))

            if self.jobTableModel.jobs[jobID].status != 1:
                browse_job.setDisabled(True)

        cursor = QCursor()
        menu.exec_(cursor.pos())


##########################################################
#############          DELEGATES             #############
##########################################################

class ProgressDelegate(QStyledItemDelegate):

    def __init__(self, view):
        super().__init__(view)

    def paint(self, painter, option, index):

        jobIDs = list(index.model().jobs.keys())
        status = getattr(index.model().jobs[jobIDs[index.row()]], "status")
        #status = .jobs[index.row()]["status"]
        if status != 1:
            return

        # startTime = index.model().jobs[index.row()]["startTime"]
        startTime = getattr(index.model().jobs[jobIDs[index.row()]], "startTime")

        # if the job did not start yet, there is not progress to show
        if startTime:
            time_elapsed = datetime.now() - datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
            #runtime = index.model().jobs[index.row()]["runTime"]
            runTime = getattr(index.model().jobs[jobIDs[index.row()]], "runTime")

            min_left = int(runTime) * 60 - time_elapsed.total_seconds() / 60

            progress = time_elapsed.total_seconds() / (int(runTime) * 3600) * 100

            opt = QStyleOptionProgressBar()
            opt.rect = option.rect
            opt.minimum = 0
            opt.maximum = 100
            opt.progress = 100 - progress
            opt.text = "%d min (%d%%)" % (min_left, round(100-progress))
            opt.textVisible = True

            if min_left <= config.MINUTES_LEFT_WHEN_WARNING_PROGRESS:
                pal = opt.palette
                col = QColor(255, 0, 0)
                pal.setColor(QPalette.Highlight, col)
                opt.palette = pal

            QApplication.style().drawControl(QStyle.CE_ProgressBar, opt, painter)


