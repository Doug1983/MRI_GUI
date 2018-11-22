"""Main.py: Loads and configures the main window for the MRI GUI application."""

__author__ = "Guillaume Doucet"

import os
import sys
from Main.BaseWidget import BaseWidget

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon


class MRI_MAIN(QMainWindow):

    def __init__(self):
        super().__init__()
        self.define_subdirectories()
        self.init_ui()

    # Subdirectories of MRI_GUI
    def define_subdirectories(self):
        basedir = os.path.dirname(os.path.realpath(__file__))
        self.icons_dir = os.path.join(basedir, 'icons')

    def init_ui(self):
        
        # Window creation ==================================================================
        self.setWindowTitle("MRI_GUI")
        self.setWindowIcon(QIcon(os.path.join(self.icons_dir, 'brain.png')))
        self.statusBar().showMessage('ready')

        # Menu Bar =========================================================================
        act_exit = QAction('&Exit', self)
        act_exit.setShortcut('Ctrl+Q')
        act_exit.setStatusTip('Exit application')
        act_exit.triggered.connect(self.quit_menu)

        brainsuite = QAction('&BrainSuite', self)
        brainsuite.triggered.connect(self.open_external_gui)

        dsi_studio = QAction('&dsistudio', self)
        dsi_studio.triggered.connect(self.open_external_gui)

        freesurfer = QAction('&freeview', self)
        freesurfer.triggered.connect(self.open_external_gui)

        slicer = QAction('&Slicer', self)
        slicer.triggered.connect(self.open_external_gui)

        trackvis = QAction('&trackvis', self)
        trackvis.triggered.connect(self.open_external_gui)

        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(act_exit)

        file_menu = menu_bar.addMenu('&External GUIs')
        file_menu.addAction(brainsuite)
        file_menu.addAction(dsi_studio)
        file_menu.addAction(freesurfer)
        file_menu.addAction(slicer)
        file_menu.addAction(trackvis)

        # GUI layout =======================================================================
        # Base widget is the parent of each sub-widget within the GUI, it holds the files info
        self.base_widget = BaseWidget(self)

        # Show Main Window
        self.setCentralWidget(self.base_widget)

        self.resize(1600, 900)
        self.show()

    # Menu methods
    def quit_menu(self):
        self.close()

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
    q_app = QApplication(sys.argv)  # application object / sys.argv are command line arguments.
    aw = MRI_MAIN()  # basic widget creation, if no parent: widget == window

    q_app.exec()  # makes sure we have a clean exit
