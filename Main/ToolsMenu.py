"""ToolsGUI is the GUI for interfacing with the different toolboxes and File I/O""" 
from PyQt5.QtWidgets import *
from PyQt5 import QtCore


class ToolsMenu(QWidget):
    update_tool_selection = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.init_ui()

    def init_ui(self):

        self.layout = QVBoxLayout(self)

        # Tools
        self.btn_group = QButtonGroup(self)
        self.layout.addWidget(QLabel('Conversion Tools: '))

        self.btn_dicom = QPushButton('DICOM to NIfTI')
        self.btn_dicom.clicked.connect(lambda: self.update_display(self.btn_dicom))
        self.btn_dicom.setCheckable(True)
        self.btn_group.addButton(self.btn_dicom)
        self.layout.addWidget(self.btn_dicom)

        self.layout.addStretch()

        self.btn_DWI_preprocess = QPushButton('Pre-Processing')
        self.btn_DWI_preprocess.clicked.connect(lambda: self.update_display(self.btn_DWI_preprocess))
        self.btn_DWI_preprocess.setCheckable(True)
        self.btn_group.addButton(self.btn_DWI_preprocess)
        self.layout.addWidget(self.btn_DWI_preprocess)

        self.btn_coregistration = QPushButton('Co-Registration')
        self.btn_coregistration.clicked.connect(lambda: self.update_display(self.btn_coregistration))
        self.btn_coregistration.setCheckable(True)
        self.btn_group.addButton(self.btn_coregistration)
        self.layout.addWidget(self.btn_coregistration)

        self.layout.addStretch()

        # Visualisation
        self.layout.addWidget(QLabel('Visualisation :'))
        self.btn_display = QPushButton('Display')
        self.btn_display.clicked.connect(lambda: self.update_display(self.btn_display))
        self.btn_display.setCheckable(True)
        self.btn_group.addButton(self.btn_display)
        self.layout.addWidget(self.btn_display)

        self.layout.addStretch()

    def update_display(self, caller):
        if caller == self.btn_dicom:
            new_tool = 'dcm2nii'
        elif caller == self.btn_DWI_preprocess:
            new_tool = 'dwipreprocess'
        elif caller == self.btn_coregistration:
            new_tool = 'coregistration'
        elif caller == self.btn_display:
            new_tool = 'display'
        else:
            new_tool = 'None'
        self.update_tool_selection.emit(new_tool)
