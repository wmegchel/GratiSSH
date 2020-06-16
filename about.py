
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class About(QDialog):

    def __init__(self):
        super(QDialog, self).__init__()
        self.setWindowTitle("About")
        self.show()

    def show(self):

        self.resize(500, 400)
        vLayout = QVBoxLayout(self)

        lab = QLabel("About GratiSSH")

        bold = QFont()
        bold.setBold(True)
        lab.setFont(bold)
        te = QTextEdit("GratiSSH v0.2 alpha.\nDeveloped by Wout Megchelenbrink")
        te.setReadOnly(True)
        te.setGeometry(50, 50, 400, 400)
        vLayout.addWidget(lab)
        vLayout.addWidget(te)


        ### Buttons
        QBtn = QDialogButtonBox.Ok  # | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        # self.buttonBox.rejected.connect(self.reject)

        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)