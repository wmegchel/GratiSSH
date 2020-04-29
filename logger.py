import config
from datetime import datetime
from PyQt5.QtGui import *

class Logger:

    def __init__(self, jobView):
        self.DBTable = config.DB.table("Log")
        self.jobView = jobView

    def writeLine(self, connectionID, jobID, message, messageType, show=True):
        jobIDx = jobID
        if jobIDx == None:
            jobIDx = 1
        #print("writing:: connectionID=%d, jobID=%d, message=%s, messageType=%s\n" % (connectionID, jobIDx, message, messageType))

        self.DBTable.insert({'connectionID': connectionID,
                  'jobID': jobID,
                  'message': message,
                  'datetime': datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                  'messageType': messageType})

        if show:
            self.writeLog(message, messageType)

    def writeLog(self, message, messageType):

        time = datetime.now().strftime("%H:%M:%S")
        messageTypes = {"INFO": "#444444", "SUCCESS": "#088a2b", "ERROR": "#c40202"}

        self.jobView.logEdit.moveCursor(QTextCursor.Start)
        self.jobView.logEdit.insertHtml("<SPAN style=\"color:%s\">%s\t%s <\SPAN><BR>" % (messageTypes[messageType], time, message))


    def clear(self, show=True):
        pass

