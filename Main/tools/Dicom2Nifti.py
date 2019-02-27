import shutil as sh

from nipype.interfaces.dcm2nii import Dcm2niix
import nipype.pipeline.engine as pe

from PyQt5.QtWidgets import QLabel, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QCheckBox, QComboBox, QLineEdit
from PyQt5 import QtCore

from tools.BaseInterface import *


class Dicom2Nifti(BaseInterface):

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent, dir_dic, bids)

        self.dcm_rows = []

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        # Options
        self.layout.addWidget(QLabel('Options: '))

        layout_options = QHBoxLayout()
        sub_1 = QVBoxLayout()
        self.chk_anon = QCheckBox("Anonymize DICOM")
        self.chk_anon.setChecked(True)
        self.chk_3D = QCheckBox("Stack 3D images")
        sub_1.addWidget(self.chk_anon)
        sub_1.addWidget(self.chk_3D)
        sub_1.addStretch()

        sub_2 = QVBoxLayout()
        self.chk_GZ = QCheckBox(".nii.gz compression")
        self.chk_GZ.setChecked(True)
        self.comp = QComboBox()
        self.comp.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        sub_2.addWidget(self.chk_GZ)
        sub_2.addWidget(QLabel('Compression (1-fast, larger files -> 9-slow, smaller files): '))
        sub_2.addWidget(self.comp)
        sub_2.addStretch()

        layout_options.addLayout(sub_1)
        layout_options.addLayout(sub_2)
        layout_options.addStretch()

        self.layout.addLayout(layout_options)
        self.file_layout_labels = QHBoxLayout()
        self.file_layout_labels.addWidget(QLabel('In File'), 3)
        self.file_layout_labels.addWidget(QLabel('Data Type'), 1)
        self.file_layout_labels.addWidget(QLabel('Subject'), 1)
        self.file_layout_labels.addWidget(QLabel('Session'), 1)
        self.file_layout_labels.addWidget(QLabel('Other'), 1)
        self.file_layout_labels.addWidget(QLabel('Scan Type'), 1)
        self.file_layout_labels.addWidget(QLabel('Out File'), 3)
        self.layout.addLayout(self.file_layout_labels)

        self.file_layout = QVBoxLayout()

        self.layout.addLayout(self.file_layout)
        self.layout.addStretch()

        self.btn_go = QPushButton("Process all files")
        self.btn_go.clicked.connect(self.go)
        self.layout.addWidget(self.btn_go)

    def update_file_selection(self, files, _):
        self.curr_files = files
        if len(self.dcm_rows) > 0:
            for row in self.dcm_rows:
                self.file_layout.removeWidget(row)
                row.close()
            self.dcm_rows.clear()

        if len(files['file_names']) > 0:

            for i in range(0, len(files['file_names'])):
                temp = Dcm2NiiRow(self)
                temp.in_file.setText(files['file_names'][i])
                temp.type.setText(files['data_types'][i])
                temp.sub.setText(files['subjects'][i])
                if files['sessions'][i] != 'Empty':
                    temp.sess.setText(files['sessions'][i])
                else:
                    temp.sess.setText('')
                temp.scan.setText(files['data_scans'][i])

                self.dcm_rows.append(temp)
                self.file_layout.addWidget(temp)
            self.file_layout.addStretch()

    # DICOM TO NII CONVERSION ===================================================================
    def go(self):
        # since the conversion takes a while, change cursor to hourglass
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        dcm_node = pe.MapNode(interface=Dcm2niix(), name='dcmnode', iterfield=['source_dir'])

        options = dict()
        options['anon_bids'] = self.chk_anon.isChecked()
        options['merge_imgs'] = self.chk_3D.isChecked()
        options['compression'] = self.comp.currentIndex()+1

        if self.chk_GZ.isChecked():
            options['compress'] = 'y'
            out_format = '.nii.gz'
        else:
            options['compress'] = 'n'
            out_format = '.nii'

        for opt, value in options.items():
            dcm_node.inputs.__setattr__(opt, value)

        # get selected files
        # since dcm2niix uses directories to convert files we will get the containing directory as input to the script
        # instead of a list of file names
        in_dirs = [os.path.split(row.in_file.text())[0] for row in self.dcm_rows]

        dcm_node.inputs.output_dir = self.dir_dic['temp_dir']
        dcm_node.inputs.source_dir = in_dirs

        dcm_node.run()

        # rename and move files into appropriate bids folders
        self.move_and_rename(dcm_node.result.outputs.bids, dcm_node.result.outputs.bvals,
                             dcm_node.result.outputs.bvecs, dcm_node.result.outputs.converted_files,
                             self.process_out_files(), out_format)

        QApplication.restoreOverrideCursor()
        self.parentWidget.post_process_update()

    def move_and_rename(self, out_bids, out_bval, out_bvec, out_nii, bids_out_files, out_format):

        for i, nii in enumerate(out_nii):

            if not os.path.isdir(os.path.split(bids_out_files[i])[0]):
                os.makedirs(os.path.split(bids_out_files[i])[0])

            if os.path.isfile(bids_out_files[i] + out_format):
                overwrite = self.overwrite_prompt(bids_out_files[i])
                if overwrite:
                    os.remove(bids_out_files[i] + out_format)
                elif not overwrite:
                    bids_out_files[i] = os.path.join(os.path.split(bids_out_files[i])[0], 'new_' +
                                                     os.path.split(bids_out_files[i])[1])
                elif overwrite is None:
                    return

            # rename and move
            sh.move(nii, bids_out_files[i] + out_format)

            if len(out_bids) > i:
                sh.move(out_bids[i], bids_out_files[i] + '.json')

            if len(out_bval) > i:
                sh.move(out_bval[i], bids_out_files[i] + '.bval')

            if len(out_bvec) > i:
                sh.move(out_bvec[i], bids_out_files[i] + '.bvec')

    def process_out_files(self):
        out_files = []
        for i, row in enumerate(self.dcm_rows):
            out_files.append(os.path.join(self.dir_dic['data_dir'], row.sub.text()))

            if row.sess.text() != '':
                out_files[i] = os.path.join(out_files[i], row.sess.text())

            out_files[i] = os.path.join(out_files[i], row.type.text(), row.out_file.text())

        return out_files


class Dcm2NiiRow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.in_file = QLineEdit()
        self.in_file.setReadOnly(True)
        self.scan = QLineEdit()
        self.scan.textChanged.connect(self.update_out_file)
        self.sub = QLineEdit()
        self.sub.textChanged.connect(self.update_out_file)
        self.sess = QLineEdit()
        self.sess.textChanged.connect(self.update_out_file)
        self.other = QLineEdit()
        self.other.textChanged.connect(self.update_out_file)
        self.type = QLineEdit()
        self.type.textChanged.connect(self.update_out_file)
        self.out_file = QLineEdit()
        self.out_file.setReadOnly(True)

        self.layout.addWidget(self.in_file, 3)
        self.layout.addWidget(self.type, 1)
        self.layout.addWidget(self.sub, 1)
        self.layout.addWidget(self.sess, 1)
        self.layout.addWidget(self.other, 1)
        self.layout.addWidget(self.scan, 1)
        self.layout.addWidget(self.out_file, 3)

    def update_out_file(self):

        out_file = self.sub.text() + '_'
        if self.sess.text() != '':
            out_file += self.sess.text() + '_'

        if self.other.text() != '':
            out_file += self.other.text() + '_'

        out_file += self.scan.text()

        self.out_file.setText(out_file)
