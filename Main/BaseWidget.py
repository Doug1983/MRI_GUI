"""BaseWidget class for the MRI_MAIN window. Will hold the file and log information.""" 
# When a button is clicked in the top menu, this class receives the signal, gets the proper data and
# updates the ToolsGUI accordingly.

# The log file contains the output and list of all processing steps undertaken on the MRI file
# It is displayed at the bottom of the main window.

from ToolsMenu import *
from FileNav import *
from ToolsInterface import *

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


class BaseWidget(QWidget):

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)

        # Tools menu
        self.tools_menu = ToolsMenu(self)
        self.layout.addWidget(self.tools_menu, 2)
        
        # File Navigator
        file_display_layout = QVBoxLayout()
        self.file_nav = FileNav(self, dir_dic, bids)
        file_display_layout.addWidget(self.file_nav, 2)

        # Tools Interface
        self.tools_interface = ToolsInterface(self, dir_dic, bids)
        file_display_layout.addWidget(self.tools_interface, 10)

        self.layout.addLayout(file_display_layout, 10)

        # GUI events
        # Tools Menu:
        # Click on tools button
        self.tools_menu.update_tool_selection.connect(self.tools_interface.update_tool_selection)
        self.tools_menu.update_tool_selection.connect(self.file_nav.update_tool_selection)

        # File Navigator:
        # Change in selected file
        self.file_nav.send_selected_files.connect(self.tools_interface.update_file_selection)

        # Tools Interface:
        # update files post-processing
        self.tools_interface.refresh_files.connect(self.file_nav.refresh_files)

        self.raise_()
