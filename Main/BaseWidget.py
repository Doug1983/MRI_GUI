"""BaseWidget class for the MRI_MAIN window. Will hold the file and log information.""" 
# When a button is clicked in the top menu, this class receives the signal, gets the proper data and
# updates the ToolsGUI accordingly.

# The log file contains the output and list of all processing steps undertaken on the MRI file
# It is displayed at the bottom of the main window.

from ToolsGUI import *
from Display import * 
from TopMenu import *

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


class BaseWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.bAll = QVBoxLayout(self)
        self.setLayout(self.bAll)

        # top menu
        self.topMenu = TopMenu(self)
        self.bAll.addWidget(self.topMenu, 0)
        
        # Left Toolbar
        b1 = QHBoxLayout()
        self.toolsGUI = ToolsGUI(self)
        b1.addWidget(self.toolsGUI, 0)
        
        # Display
        self.display = Display(self)
        b1.addWidget(self.display, 10)
        self.bAll.addLayout(b1)

        # GUI events
        self.topMenu.convertDICOM.connect(self.toolsGUI.preprocess_dicom)
        self.topMenu.loadData.connect(self.toolsGUI.load_data)
        self.topMenu.eddyCorr.connect(self.toolsGUI.preprocess_eddy)
        self.topMenu.sigBET.connect(self.toolsGUI.preprocess_bet)

        self.toolsGUI.postProcessDisplayUpdateSignal.connect(self.display.postProcessUpdate)
        self.raise_()

