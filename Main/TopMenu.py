
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PyQt5 import QtCore


class TopMenu(QWidget):
    convertDICOM = QtCore.pyqtSignal()
    loadData = QtCore.pyqtSignal()
    eddyCorr = QtCore.pyqtSignal()
    sigBET = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parentWidget = parent  # Should always be the BaseWidget
        self.init_ui()

    def init_ui(self):

        self.layout = QHBoxLayout(self)

        self.btnDICOM = QPushButton("DICOM -> NIfTI")
        self.btnDICOM.clicked.connect(self.convertDICOMClicked)
        self.layout.addWidget(self.btnDICOM)

        self.btnNii = QPushButton("Load NIfTI")
        self.btnNii.clicked.connect(self.loadNIfTIClicked)
        self.btnNii.setEnabled(True)
        self.layout.addWidget(self.btnNii)
        
        self.btnEddy = QPushButton("Eddy Current Correction")
        self.btnEddy.clicked.connect(self.eddyClicked)
        self.btnEddy.setEnabled(True)
        self.layout.addWidget(self.btnEddy)
    
        self.btnBET = QPushButton("Brain Extraction")
        self.btnBET.clicked.connect(self.betClicked)
        self.btnBET.setEnabled(True)
        self.layout.addWidget(self.btnBET)

        self.layout.addStretch()

    def convertDICOMClicked(self):
        self.convertDICOM.emit()

    def loadNIfTIClicked(self):
        self.loadData.emit()

    def eddyClicked(self):
        self.eddyCorr.emit()
    
    def betClicked(self):
        self.sigBET.emit()
