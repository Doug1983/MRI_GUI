"""ToolsGUI is the GUI for interfacing with the different toolboxes and File I/O""" 

import os
import re

from collections import defaultdict
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import BET, EddyCorrect


class ToolsGUI(QWidget):
    postProcessDisplayUpdateSignal = QtCore.pyqtSignal(list, str, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.baseDir = ''
        self.allSubDirs = []  # Subdirectories in the DICOM folder
        self.logFile = ''
        # can be split over multiple files, saves a dict:
        #  if file names are File-####.dcm will save: {'File-' : [1, max(####)]}
        self.allDICOM = defaultdict(list)
        self.allNii = []

        # there is one issue with FSL scripts: they don't accept spaces in the file paths so if the folder contains
        # white spaces we must create a temporary folder to move the file there, compute, and move back.
        # create temporary folder in main drive
        # since we run inside a container, an absolute path can be defined
        self.temp_dir = os.path.join('/tmp', 'MRI_temp')
        if not os.path.isdir(self.temp_dir):
            os.mkdir(self.temp_dir)

        self.initUI()

    def initUI(self):
        # all QT widgets
        self.fileNavWidget = FileNavigator(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.fileNavWidget)
        # add a QStack to hold all the possible GUIs
        self.stack = QStackedWidget(self)
        self.blank = BlankWidget(self)
        self.DICOM = ConvertDICOM(self)
        self.Eddy = EddyCorrection(self)
        self.BET = BetWidget(self)
        self.stack.addWidget(self.blank)
        self.stack.addWidget(self.DICOM)
        self.stack.addWidget(self.Eddy)
        self.stack.addWidget(self.BET)
        self.stack.setCurrentIndex(0)
        self.layout.addWidget(self.stack)
        self.layout.addStretch()

        self.DICOM.process_data.connect(self.process_data_folder)
        self.Eddy.process_data.connect(self.process_data_files)
        self.BET.process_data.connect(self.process_data_files)
    
    # DICOM TO NII CONVERSION ===================================================================
    # Sets the GUI up for option selection and select directory to process
    def preprocess_dicom(self):
        # open file dialog to select base directory containing DICOM data
        self.baseDir = self.getDirectory('Select directory containing DICOM files')

        # scan dir to find DICOM, log and sub-folders
        if self.baseDir != '':
            self.scanDirectory(self.baseDir)
            self.updateGUI(1)
            self.updateFileNavigator(['.dcm'])
        else:
            print('No dir selected')

    # EDDY current correction ===================================================================
    def preprocess_eddy(self):
        self.updateGUI(2)

    # BET =======================================================================================
    def preprocess_bet(self):
        self.updateGUI(3)

    # Class functions
    def process_data_folder(self, analysis, options):
        # since the conversion takes a while, change cursor to hourglass
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        if analysis == 'Dcm2nii':
            process = Dcm2niix()
        else:
            process = []

        for opt, value in options.items():
            process.inputs.__setattr__(opt, value)

        if not os.path.isdir(os.path.join(self.baseDir, analysis.capitalize())):
            os.mkdir(os.path.join(self.baseDir, analysis.capitalize()))

        process.inputs.source_dir = self.baseDir
        process.inputs.output_dir = os.path.join(self.baseDir, analysis.capitalize())

        try:
            out = process.run()
        except RuntimeError as err:
            self.logFile += str(err)
        else:
            self.logFile += out.runtime.stdout

        # update GUI
        self.scanDirectory(self.baseDir)
        self.updateGUI(0)
        self.updateFileNavigator(['.nii'])

        QApplication.restoreOverrideCursor()
        self.postProcessDisplayUpdate()

    def process_data_files(self, analysis, options):

        # since the conversion takes a while, change cursor to hourglass
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        if analysis == 'eddy':
            process = EddyCorrect()
        elif analysis == 'bet':
            process = BET()
        else:
            process = []

        for opt, value in options.items():
            process.inputs.__setattr__(opt, value)

        # get selected files
        in_files, out_files, temp_files = self.return_selected_files(analysis)

        for in_file, out_file, temp_file in zip(in_files, out_files, temp_files):

            if not os.path.isdir(os.path.split(out_file)[0]):
                os.mkdir(os.path.split(out_file)[0])

            process.inputs.in_file = in_file
            process.inputs.out_file = out_file

            if os.path.isfile(out_file):
                overwrite = self.overwrite_prompt(out_file)
                if not overwrite:
                    out_file = os.path.join(os.path.split(out_file)[0], 'new_' + os.path.split(out_file)[1])
                elif overwrite is None:
                    return
            try:
                out = process.run()
            except RuntimeError as err:
                self.logFile += str(err)
            else:
                self.logFile += out.runtime.stdout
                if temp_file:
                    self.move_from_temp(out_file)
            if temp_file:
                self.move_from_temp(in_file)

        # update GUI
        self.scanDirectory(self.baseDir)
        self.updateGUI(0)
        self.updateFileNavigator(['.nii'])

        QApplication.restoreOverrideCursor()
        self.postProcessDisplayUpdate()

    def postProcessDisplayUpdate(self):
        self.postProcessDisplayUpdateSignal.emit(self.allNii, self.logFile, self.baseDir)

    def load_data(self):
        # open file dialog to select base directory containing DICOM data
        self.baseDir = self.getDirectory('Select base directory')

        # scan dir to find DICOM, log and sub-folders
        if self.baseDir != '':
            self.scanDirectory(self.baseDir)
            self.updateGUI(0)
            self.updateFileNavigator(['.nii'])
            self.postProcessDisplayUpdate()
        else:
            print('No dir selected')

    def updateGUI(self, new_gui):
        self.stack.setCurrentIndex(new_gui)
        
    def updateFileNavigator(self, file_filter):
        self.fileNavWidget.fileNav.clear()
        if '.dcm' in file_filter:
            for File, Nbr in self.allDICOM.items():
                self.fileNavWidget.fileNav.addItem(File + "[" + str(Nbr[0]) + ":" + str(Nbr[1]) + "].dcm")
        if '.nii' in file_filter:
            for File in self.allNii:
                self.fileNavWidget.fileNav.addItem(File)
        else:
            # bogus statement to allow proper code folding
            bogus = None 

    def getDirectory(self, prompt_title):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setWindowTitle(prompt_title)
        if dlg.exec_():
            files = dlg.selectedFiles()
            return os.path.abspath(files[0])
        else:
            return ''

    def scanDirectory(self, directory):
        # clear current directory info
        self.allDICOM = defaultdict(list)
        self.logFile = ''
        self.allNii = []
        self.allSubDirs = []

        # reg ex for dicom files
        regex = re.compile('(?P<File>.*\D)(?P<Nbr>\d*)(?P<ext>.dcm)$')
        # walk through all sub-folders
        for root, dirs, files in os.walk(directory):

            # need to remove the first separators and the base directory
            if root == directory:
                tempDir = ''
            else:
                tempDir = root.replace(directory+os.sep, '')

            for file in files:
                tempFile = os.path.join(tempDir, file)
                if '.dcm' in tempFile:
                    match = regex.match(tempFile)
                    if not match.group('File') in self.allDICOM:
                        self.allDICOM[match.group('File')] = [1, 1]
                    else:
                        self.allDICOM[match.group('File')][1] = int(match.group('Nbr'))
                elif '.log' in tempFile:
                    self.logFile = tempFile
                elif '.nii' in tempFile and tempFile not in self.allNii:
                    self.allNii.append(tempFile)

            for dir in dirs:
                self.allSubDirs.append(os.path.join(tempDir, dir))

    def return_selected_files(self, analysis):

        # get selected file from the file navigator
        list_files = self.fileNavWidget.fileNav.selectedItems()

        in_files = []
        out_files = []
        temp_files = []

        for file in list_files:
            if file.text() != 'None':
                if ' ' in self.baseDir:

                    full_in_path = os.path.join(self.baseDir, file.text())
                    temp_in_path = os.path.join(self.temp_dir, file.text())
                    temp_out_path = os.path.join(self.temp_dir, os.path.split(file.text())[0],
                                                 analysis.capitalize(),
                                                 analysis.lower()[0:3] + '_' + os.path.split(file.text())[1])

                    # move .nii file to temporary folder
                    os.rename(full_in_path, temp_in_path)
                    temp_files.append(True)
                else:
                    temp_in_path = os.path.join(self.baseDir, file.text())
                    temp_out_path = os.path.join(self.baseDir, os.path.split(file.text())[0],
                                                 analysis.capitalize(),
                                                 analysis.lower()[0:3] + '_' + os.path.split(file.text())[1])
                    temp_files.append(False)

                in_files.append(temp_in_path)
                out_files.append(temp_out_path)

        return in_files, out_files, temp_files

    def move_from_temp(self, temp_file):

        # move files back to the original directory
        base_file = temp_file.replace(self.temp_dir, self.baseDir)

        if os.path.isfile(base_file):
            ovr = self.overwrite_prompt(base_file)

            if ovr:
                os.remove(base_file)
                os.rename(temp_file, base_file)
            elif not ovr:
                os.rename(temp_file, os.path.join(os.path.split(base_file)[0], 'new_' + os.path.split(base_file)[1]))
            else:
                return

    @staticmethod
    def overwrite_prompt(out_file):
        over_box = QMessageBox()
        over_box.setIcon(QMessageBox.Critical)
        over_box.setText("File " + os.path.split(out_file)[1] + " already exists. Overwrite?")
        over_box.setInformativeText("Not overwriting will create a new file.")
        over_box.setWindowTitle("Overwrite file?")
        over_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        box_answer = over_box.exec_()

        if box_answer == QMessageBox.Yes:
            return True
        elif box_answer == QMessageBox.No:
            return False
        else:
            return None


# Widgets ========================================================================================================
class ConvertDICOM(QWidget):
    process_data = QtCore.pyqtSignal(str, dict)  # connects to ToolsGUI

    def __init__(self,parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        # Options
        self.chkAnon = QCheckBox("Anonymize DICOM")
        self.chk3D = QCheckBox("Stack 3D images")
        lbl = QLabel('Compression: 1-fast, larger files -> 9-slow, smaller files')
        self.comp = QComboBox()
        self.comp.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.chkGZ = QCheckBox(".nii.gz compression")
        self.btnGo = QPushButton("Process all files")
        layout.addWidget(self.chkAnon)
        layout.addWidget(self.chk3D)
        layout.addWidget(lbl)
        layout.addWidget(self.comp)
        layout.addWidget(self.chkGZ)
        layout.addStretch()
        layout.addWidget(self.btnGo)
        layout.addStretch()
        self.setLayout(layout)

        self.btnGo.clicked.connect(self.go)

    def go(self):
        analysis = 'Dcm2nii'
        options = dict()
        options['anon_bids'] = self.chkAnon.isChecked()
        options['merge_imgs'] = self.chk3D.isChecked()
        options['compression'] = self.comp.currentIndex()+1

        if self.chkGZ.isChecked():
            options['compress'] = 'y'
        else:
            options['compress'] = 'n'

        self.process_data.emit(analysis, options)


class EddyCorrection(QWidget):
    process_data = QtCore.pyqtSignal(str, dict)  # connects to ToolsGUI

    def __init__(self,parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.initUI()

    def initUI(self):
        # since we do not have the proper scans to use the "eddy" function
        # we use the previous version of eddy_correct which doesnt require specific
        # arguments.
        layout = QVBoxLayout(self)
        # Options
        layout.addWidget(QLabel("Select DWI image in the file navigator and click Process button"))
        self.btnGo = QPushButton("Process")
        layout.addWidget(self.btnGo)
        layout.addStretch()
        self.setLayout(layout)

        self.btnGo.clicked.connect(self.go)

    def go(self):
        analysis = 'eddy'
        options = dict()
        self.process_data.emit(analysis, options)


class BetWidget(QWidget):
    process_data = QtCore.pyqtSignal(str, dict)  # connects to ToolsGUI

    def __init__(self,parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        # Options
        b1 = QHBoxLayout()
        b1.addWidget(QLabel("Fractional intensity threshold: "))
        self.spinFracThresh = QDoubleSpinBox(self)
        self.spinFracThresh.setMinimum(0.1)
        self.spinFracThresh.setMaximum(1)
        self.spinFracThresh.setValue(0.5)
        self.spinFracThresh.setSingleStep(0.05)
        b1.addWidget(self.spinFracThresh)
        layout.addLayout(b1)
        self.chkOutput=QCheckBox("Output brain-extracted image")
        self.chkOutput.setChecked(True)
        self.chkBinaryMask=QCheckBox("Output binary brain mask image")
        self.chkApplyMask=QCheckBox("Apply thresholding to segmented brain image and mask")
        self.chk_mesh = QCheckBox("Generate brain mesh surface")
        self.chkSkull=QCheckBox("Generate rough skull image")

        layout.addWidget(self.chkOutput)
        layout.addWidget(self.chkBinaryMask)
        layout.addWidget(self.chkApplyMask)
        layout.addWidget(self.chk_mesh)
        layout.addWidget(self.chkSkull)

        self.btnGo = QPushButton("Process selected files")
        layout.addWidget(self.btnGo)
        layout.addStretch()
        self.setLayout(layout)

        self.btnGo.clicked.connect(self.go)

    def go(self):
        analysis = 'bet'
        # BET options
        options = dict()
        options['frac'] = self.spinFracThresh.value()
        options['mask'] = self.chkBinaryMask.isChecked()
        options['skull'] = self.chkSkull.isChecked()
        options['threshold'] = self.chkApplyMask.isChecked()
        options['mesh'] = self.chk_mesh.isChecked()
        options['no_output'] = not self.chkOutput.isChecked()

        self.process_data.emit(analysis, options)
      

class BlankWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)


class FileNavigator(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        b1 = QVBoxLayout(self)
        self.fileNavLab = QLabel("Files to process:")
        self.fileNavLab.setAlignment(QtCore.Qt.AlignCenter)
        b1.addWidget(self.fileNavLab)
        self.fileNav = QListWidget(self)
        self.fileNav.addItem("None")
        self.fileNav.setCurrentRow(0)
        self.fileNav.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fileNav.setFont(QFont('Times', 12))
        b1.addWidget(self.fileNav)
        b1.addStretch()
        self.setLayout(b1)
