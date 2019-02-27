from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from PyQt5 import QtCore
from tools.Dicom2Nifti import Dicom2Nifti
from tools.DwiPreProcess import DwiPreProcess
from tools.CoRegistration import CoRegistration
from tools.Display import Display

from tools.BaseInterface import BaseInterface


class ToolsInterface(QWidget):
    refresh_files = QtCore.pyqtSignal()

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # add a QStack to hold all the possible GUIs
        self.stack = QStackedWidget(self)
        self.blank = BaseInterface(self, dir_dic, bids)
        self.dicom = Dicom2Nifti(self, dir_dic, bids)
        self.display = Display(self, dir_dic, bids)
        self.dwi_pre_process = DwiPreProcess(self, dir_dic, bids)
        self.co_registration = CoRegistration(self, dir_dic, bids)

        self.stack.addWidget(self.blank)
        self.stack.addWidget(self.display)
        self.stack.addWidget(self.dicom)
        self.stack.addWidget(self.dwi_pre_process)
        self.stack.addWidget(self.co_registration)

        self.stack.setCurrentIndex(0)
        self.layout.addWidget(self.stack)

    @QtCore.pyqtSlot(str)
    def update_tool_selection(self, new_tool):
        if new_tool == 'dcm2nii':
            self.stack.setCurrentWidget(self.dicom)
        if new_tool == 'display':
            self.stack.setCurrentWidget(self.display)
        if new_tool == 'dwipreprocess':
            self.stack.setCurrentWidget(self.dwi_pre_process)
        if new_tool == 'coregistration':
            self.stack.setCurrentWidget(self.co_registration)

        if new_tool == 'None':
            self.stack.setCurrentWidget(self.blank)

    @QtCore.pyqtSlot(dict, dict)
    def update_file_selection(self, selected_files, template_files):
        self.stack.currentWidget().update_file_selection(selected_files, template_files)

    def post_process_update(self):
        self.refresh_files.emit()
