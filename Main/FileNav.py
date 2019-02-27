from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QAbstractItemView
from PyQt5 import QtCore


class FileNav(QWidget):
    send_selected_files = QtCore.pyqtSignal(dict, dict)

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent)
        self.parentWidget = parent  # Should always be the BaseWidget
        self.dir_dic = dir_dic
        self.bids = bids

        # Data
        self.curr_subjects = self.bids.return_subjects()

        self.curr_subject = ''
        self.curr_sessions = ''
        self.curr_scans = ''
        self.curr_file = ''

        self.curr_files = dict()
        self.filters = dict()
        self.filters['subjects'] = 'DEFAULTNOSELECTION'

        # to avoid updates from modifications of the UI elements when reading files
        self.skip_update = False
        self.init_ui()

    def init_ui(self):
        self.layout = QHBoxLayout(self)

        # subject selection
        temp_layout = QVBoxLayout()
        temp_layout.addWidget(QLabel('Subjects: '))
        self.list_subjects = QListWidget(self)
        self.list_subjects.addItems(self.curr_subjects)
        self.list_subjects.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_subjects.currentItemChanged.connect(self.update_subject)
        temp_layout.addWidget(self.list_subjects)
        self.layout.addLayout(temp_layout)

        temp_layout = QVBoxLayout()
        temp_layout.addWidget(QLabel('Sessions: '))
        self.list_sessions = QListWidget(self)
        self.list_sessions.addItem('All')
        self.list_sessions.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_sessions.itemSelectionChanged.connect(self.update_sessions)
        temp_layout.addWidget(self.list_sessions)
        self.layout.addLayout(temp_layout)

        temp_layout = QVBoxLayout()
        temp_layout.addWidget(QLabel('Files: '))
        self.list_files = QListWidget(self)
        self.list_files.addItem('All')
        self.list_files.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_files.itemSelectionChanged.connect(self.return_selected_files)
        temp_layout.addWidget(self.list_files)
        self.layout.addLayout(temp_layout, 2)

        self.layout.addStretch()

    def walk_files(self):
        self.bids.walk_path(self.dir_dic['data_dir'])

    @QtCore.pyqtSlot()
    def refresh_files(self):
        self.walk_files()
        self.update_subject()

    def update_subject(self):
        self.filters['subjects'] = self.list_subjects.currentItem().text()

        # remove sessions and files filters
        if 'sessions' in self.filters:
            del self.filters['sessions']
        if 'file_names' in self.filters:
            del self.filters['file_names']

        self.get_files_from_filters('sub')

    def update_sessions(self):
        if not self.skip_update:
            if 'file_names' in self.filters:
                del self.filters['file_names']

            self.filters['sessions'] = [sess.text() for sess in self.list_sessions.selectedItems()]
            if not self.filters['sessions']:
                del self.filters['sessions']

            self.get_files_from_filters('sess')

    def get_files_from_filters(self, update_from):
        self.skip_update = True
        all_files = self.bids.return_files(self.filters)

        if update_from in ['sub', 'tool']:
            # update sessions
            self.list_sessions.clear()

            for sess_id, sess in enumerate(set(all_files['sessions'])):
                self.list_sessions.addItem(sess)
                self.list_sessions.setCurrentItem(self.list_sessions.item(sess_id))

        if update_from in ['sub', 'sess', 'tool']:
            # update files
            self.list_files.clear()
            self.list_files.addItems(set(all_files['file_names']))
            self.list_files.selectAll()

        self.skip_update = False
        self.return_selected_files()

    @QtCore.pyqtSlot(str)
    def update_tool_selection(self, new_tool):
        # will use new tool selection to filter file types and scans
        if 'data_scans' in self.filters:
            del self.filters['data_scans']
        if 'data_types' in self.filters:
            del self.filters['data_types']
        if 'file_names' in self.filters:
            del self.filters['file_names']

        if new_tool == 'dcm2nii':
            self.list_files.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.filters['data_sources'] = 'sourcedata'
            self.filters['formats'] = 'dicom'

        elif new_tool == 'display':
            self.list_files.setSelectionMode(QAbstractItemView.SingleSelection)
            self.filters['data_sources'] = ['raw', 'derivatives']
            self.filters['formats'] = ['nifti']

        elif new_tool in ['dwipreprocess', 'coregistration']:
            self.list_files.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.filters['data_sources'] = ['raw', 'derivatives']
            self.filters['formats'] = ['nifti']

        self.get_files_from_filters('tool')

    def return_selected_files(self):
        if not self.skip_update:
            self.filters['file_names'] = [file.text() for file in self.list_files.selectedItems()]
            data_files = self.bids.return_files(self.filters)

            template_files = self.bids.return_files({'data_sources': 'templates'})
            self.send_selected_files.emit(data_files, template_files)
