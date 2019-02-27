"""
Main.py: Loads and configures the main window for the MRI GUI application.

Holds the directory structures and the BidsParser object to allow data folder changes from the UI.

"""

__author__ = "Guillaume Doucet"

import os
import sys
from BaseWidget import BaseWidget

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from bidsparser import Parser


class MRI_MAIN(QMainWindow):

    def __init__(self):
        super().__init__()

        # Subdirectories of MRI_GUI ========================================================
        # instance directory of sub-folders, they will be modifiable through the GUI
        self.dir_dic = dict()

        self.dir_dic['base_dir'] = os.path.dirname(os.path.realpath(__file__))
        self.dir_dic['icons_dir'] = os.path.join(self.dir_dic['base_dir'], 'icons')

        self.dir_dic['data_dir'] = '/mnt/data'
        self.dir_dic['templates_dir'] = '/mnt/data/templates'

        # when functions don't accept output files as options we will output by
        # default to a temporary directory and move the files
        # self.dir_dic['temp_dir'] = os.path.join('/tmp', 'MRI_temp')
        self.dir_dic['temp_dir'] = os.path.join('/mnt/data', 'MRI_temp')
        if not os.path.isdir(self.dir_dic['temp_dir']):
            os.mkdir(self.dir_dic['temp_dir'])

        # Bids Parser initialization =======================================================
        self.bids = Parser()
        self.bids.walk_path(self.dir_dic['data_dir'])

        # UI Initialization ================================================================
        # Window creation
        self.setWindowTitle("MRI_GUI")
        self.setWindowIcon(QIcon(os.path.join(self.dir_dic['icons_dir'], 'brain.png')))
        self.statusBar().showMessage('ready')

        # Menu Bar
        act_exit = QAction('&Exit', self)
        act_exit.setShortcut('Ctrl+Q')
        act_exit.setStatusTip('Exit application')
        act_exit.triggered.connect(self.quit_menu)

        slicer = QAction('&Slicer', self)
        slicer.triggered.connect(self.open_external_gui)

        trackvis = QAction('&trackvis', self)
        trackvis.triggered.connect(self.open_external_gui)

        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(act_exit)

        file_menu = menu_bar.addMenu('&External GUIs')
        file_menu.addAction(slicer)
        file_menu.addAction(trackvis)

        # GUI layout
        # Base widget is the parent of each sub-widget within the GUI: ToolsMenu, ToolsInterface and FileNav
        # passing the directory dictionary and the bids parser handle
        self.base_widget = BaseWidget(self, self.dir_dic, self.bids)

        # Show Main Window
        self.setCentralWidget(self.base_widget)

        self.resize(1600, 900)
        self.setFixedSize(self.size())
        self.show()

    # Menu methods
    @QtCore.pyqtSlot()
    def quit_menu(self):
        self.close()

    @QtCore.pyqtSlot()
    def open_external_gui(self):
        import subprocess

        gui = self.sender().text()

        bash_command = ['/opt/'+gui[1:]]
        output = subprocess.run(bash_command, stdout=subprocess.PIPE)

    # Main Window events
    def closeEvent(self, event):
        # self, window title, Message, choices, default option
        reply = QMessageBox.question(self, 'Confirm', "Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        
if __name__ == '__main__':
    # QStandardPaths error
    if not os.path.isdir('/tmp/runtime-root'):
        os.mkdir('/tmp/runtime-root')
    os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-root'
    os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'

    # FSL needs a user environment variable
    os.environ['USER'] = 'neuro'
    os.environ['DISPLAY'] = '172.23.200.33:0.0'
    # brainsuite path added to the environment in case it's not there
    # if 'BrainSuite' not in os.environ['PATH']:
    #     os.environ['PATH'] = os.environ['PATH'] + ':/opt/BrainSuite18a/bin:/opt/BrainSuite18a/bdp'

    q_app = QApplication(sys.argv)  # application object / sys.argv are command line arguments.
    aw = MRI_MAIN()  # basic widget creation, if no parent: widget == window

    q_app.exec()  # makes sure we have a clean exit
    closed = 2
