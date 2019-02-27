import os
import fnmatch as fn

from traits.trait_base import _Undefined

from PyQt5.QtWidgets import QWidget, QMessageBox, QHBoxLayout, QVBoxLayout, QComboBox, QLabel
from tools.set_params import GUIParameters


class BaseInterface(QWidget):
    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent)
        self.parentWidget = parent
        self.dir_dic = dir_dic
        self.bids = bids

        # Interfaces List
        self.interfaces = []
        self.required_files = dict()
        self.optional_files = dict()

        # currently selected files
        self.curr_files = dict()
        self.template_files = dict()
        self.node_to_btn_map = dict()

    def update_file_selection(self, data_files, template_files):
        self.curr_files = data_files
        self.template_files = template_files
        self.populate_files()

    @staticmethod
    def generate_out_name(in_name, appendix, to_replace, ext):

        if to_replace is None:
            temp = in_name.partition('.')
            out_name = temp[0] + appendix + temp[1] + temp[2]
        else:
            temp = in_name.partition(to_replace)
            out_name = temp[0] + appendix + temp[2]

        return out_name

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

    def ui_set_params(self):
        caller_string = self.sender().text()

        node = [x for x in self.interfaces if x.btn_string == caller_string][0]

        # receives the nipype input specs
        lst_inputs = node.inputs.editable_traits()

        # dict containing data type, default value and description for each parameter
        dict_inputs = dict()
        # if hasattr(node.inputs, '_xor_inputs'):
        #    xor_inputs = list(getattr(node.inputs, '_xor_inputs'))

        # else:
        xor_inputs = list()

        # TODO: Better implementation of mutually exclusive parameters (e.g. crop_list xor t_min, t_size, x_min, ... )
        # in FSL extract ROI
        for spec in lst_inputs:
            if node.inputs.trait(spec).xor is not None and not any([spec in x for x in xor_inputs]):
                if spec in node.inputs.trait(spec).xor:
                    xor_inputs.append(list(node.inputs.trait(spec).xor))
                else:
                    xor_inputs.append([spec] + list(node.inputs.trait(spec).xor))

            if type(getattr(node.inputs, spec)) != _Undefined:
                dict_inputs[spec] = [type(getattr(node.inputs, spec)), getattr(node.inputs, spec),
                                     node.inputs.trait(spec).desc]
            elif hasattr(node.inputs.trait(spec).trait_type, 'evaluate'):
                if node.inputs.trait(spec).trait_type.evaluate is not None:
                    dict_inputs[spec] = [node.inputs.trait(spec).trait_type.evaluate,
                                         node.inputs.trait(spec).default,
                                         node.inputs.trait(spec).desc]
                elif type(node.inputs.trait(spec).trait_type.values) == tuple:
                    dict_inputs[spec] = [node.inputs.trait(spec).trait_type.values,
                                         node.inputs.trait(spec).default,
                                         node.inputs.trait(spec).desc]

        # will send this to the window widget to create a GUI and allow users to set values
        # remove any non editable xor_inputs
        for xor in [x for j in xor_inputs for x in j]:
            if xor not in dict_inputs:
                dict_inputs[xor] = [bytes(), 'None', xor]

        gui = GUIParameters(dict_inputs, xor_inputs)
        gui.exec_()

        # skip parameters that weren't set
        for inp in gui.out_dict:
            if inp in xor_inputs and \
                    (dict_inputs[inp][0](gui.out_dict[inp]) is False or dict_inputs[inp][0](gui.out_dict[inp]) == ''):
                continue
            else:
                # parse input into proper format (i.e. list item [0] in dict_inputs
                if type(dict_inputs[inp][0]) is tuple:
                    setattr(node.inputs, inp, (gui.out_dict[inp]))
                else:
                    setattr(node.inputs, inp, dict_inputs[inp][0](gui.out_dict[inp]))

    def return_interface(self, name):
        out = [x for x in self.interfaces if x.name == name]
        if len(out) > 0:
            return out[0]
        else:
            return None

    def populate_files(self):  # required/optional files are dicts {label: {file filters}}

        if len(self.curr_files) != 0 and hasattr(self, 'files_layout'):
            # loop through files_layout (i.e. a list of BoxLayouts containing label and combobox)
            for idx in range(self.files_layout.count()):
                if type(self.files_layout.itemAt(idx)) is QHBoxLayout:
                    # the first widget is the label, second is the combobox
                    o = self.files_layout.itemAt(idx).itemAt(1).widget()
                    if hasattr(o, 'name'):
                        # set items to be current file names
                        o.clear()

                        if 'template'.upper() in o.name.upper():
                            o.addItems([os.path.split(x)[1] for x in self.template_files['file_names']])
                            curr_files = self.template_files
                        else:
                            o.addItems([os.path.split(x)[1] for x in self.curr_files['file_names']])
                            curr_files = self.curr_files
                        o.addItem('None                                                                  ')

                        # select the proper file according to filter
                        if o.name in self.required_files:
                            o.setCurrentIndex(self.return_idx_from_filter(curr_files, self.required_files[o.name]))
                        elif o.name in self.optional_files:
                            o.setCurrentIndex(self.return_idx_from_filter(curr_files, self.optional_files[o.name]))
                        else:
                            o.setCurrentIndex(0)

    @staticmethod
    def generate_files_ui(req_files, opt_files):
        v_box = QVBoxLayout()
        v_box.addWidget(QLabel('Required Files: '))

        # loop through all required and options files to create GUI components
        for lbl in req_files.keys():
            h_box = QHBoxLayout()
            h_box.addWidget(QLabel(lbl))
            temp_combo = QComboBox()
            temp_combo.name = lbl
            temp_combo.addItem('None')
            h_box.addWidget(temp_combo)
            v_box.addLayout(h_box)

        v_box.addStretch()

        v_box.addWidget(QLabel('Optional Files: '))
        # loop through all required and options files to create GUI components
        for lbl in opt_files.keys():
            h_box = QHBoxLayout()
            h_box.addWidget(QLabel(lbl))
            temp_combo = QComboBox()
            temp_combo.name = lbl
            temp_combo.addItem('None')
            h_box.addWidget(temp_combo)
            v_box.addLayout(h_box)

        v_box.addStretch()
        return v_box

    @staticmethod
    def return_idx_from_filter(files_dict, filter_dict):

        # added fnmatch to support wildcards as processed files aren't in the
        # options (e.g. sub-01_T1w_brain.nii.gz) would allow to find brain extracted T1w.
        idx = set([i for i in range(len(files_dict['file_names']))])

        for key, value in filter_dict.items():
            if key == 'options':
                for val in value:
                    idx = idx.intersection(set(
                        [i for i, x in enumerate(files_dict[key]) if any(fn.fnmatch(y.upper(), val.upper())
                                                                         for y in files_dict[key][i])]))
                    # idx = idx.intersection(set(
                    #     [i for i, x in enumerate(files_dict[key]) if any(val.upper() == y.upper()
                    #                                                      for y in files_dict[key][i])]))
            else:
                temp = (set([i for i, x in enumerate(files_dict[key]) if fn.fnmatch(x.upper(), value.upper())]))
                # temp = (set([i for i, x in enumerate(files_dict[key]) if x.upper() == value.upper()]))
                idx = idx.intersection(temp)

        if len(idx) == 0 and len(files_dict['file_names']) > 0:
            idx = len(files_dict['file_names'])
        elif len(idx) == 0 and len(files_dict['file_names']) == 0:
            idx = 0
        else:
            idx = list(idx)[0]
        return idx
