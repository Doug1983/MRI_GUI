from PyQt5.QtWidgets import QDialog, QLineEdit, QCheckBox, QLabel, QFormLayout, QPushButton, QComboBox, QStackedWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIntValidator, QDoubleValidator


class GUIParameters(QDialog):
    def __init__(self, dict_inputs, xor_inputs):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Enter interface parameters')
        self.dict_inputs = dict_inputs
        self.xor_inputs = xor_inputs
        self.all_xor = [x for j in xor_inputs for x in j]
        self.out_dict = dict()

        # generate ui
        # dict_inputs : ['parameter name'] = [default type, default value, description]
        self.lay = QFormLayout(self)

        for inp in dict_inputs:

            if dict_inputs[inp][0] in [str]:
                setattr(self, inp, self.return_text_handle(dict_inputs[inp]))

            elif dict_inputs[inp][0] in [float]:
                setattr(self, inp, self.return_text_handle(dict_inputs[inp]))
                getattr(self, inp).setValidator(QDoubleValidator())

            elif dict_inputs[inp][0] in [int]:
                setattr(self, inp, self.return_text_handle(dict_inputs[inp]))
                getattr(self, inp).setValidator(QIntValidator())

            elif dict_inputs[inp][0] in [bool]:
                setattr(self, inp, self.return_bool_handle(dict_inputs[inp]))

            elif type(dict_inputs[inp][0]) == tuple:
                setattr(self, inp, self.return_tuple_handle(dict_inputs[inp]))
            else:
                setattr(self, inp, QLabel(inp))
                getattr(self, inp).setEnabled(False)

            if inp not in self.all_xor:
                self.lay.addRow(inp, getattr(self, inp))

        # loop through all xor inputs and generate combo boxes and fields
        for pair in xor_inputs:
            handle = self.return_xor_handle(pair)
            self.lay.addRow(handle)

        self.btn_ok = QPushButton('Ok')
        self.btn_ok.clicked.connect(self.go)
        self.lay.addRow('', self.btn_ok)

    def return_text_handle(self, lst_properties):
        out_handle = QLineEdit(self)
        out_handle.setText(str(lst_properties[1]))
        out_handle.setToolTip(lst_properties[2])

        return out_handle

    def return_bool_handle(self, lst_properties):
        out_handle = QCheckBox(self)
        out_handle.setText(' ')
        out_handle.setChecked(bool(lst_properties[1]))
        out_handle.setToolTip(lst_properties[2])

        return out_handle

    def return_tuple_handle(self, lst_properties):
        out_handle = QComboBox(self)
        out_handle.addItem('')
        out_handle.addItems([str(x) for x in lst_properties[0]])
        out_handle.setCurrentText(str(lst_properties[1]))
        out_handle.setToolTip(str(lst_properties[2]))

        return out_handle

    def return_xor_handle(self, pair):
        out_layout = QVBoxLayout()
        out_layout.addWidget(QLabel(' // '.join(pair)))

        selector = QComboBox()
        selector.addItem('')
        selector.addItems(pair)

        out_layout.addWidget(selector)

        stack = QStackedWidget()
        stack.addWidget(QLabel(''))
        for pa in pair:
            stack.addWidget(getattr(self, pa))
        out_layout.addWidget(stack)

        selector.currentIndexChanged.connect(stack.setCurrentIndex)

        return out_layout

    @pyqtSlot()
    def go(self):
        for inp in self.dict_inputs:
            obj = getattr(self, inp)
            if obj.isEnabled() and obj.isVisible():
                if self.dict_inputs[inp][0] in [str, float, int]:

                    # do not add setting if unchanged from default value
                    if str(self.dict_inputs[inp][1]) != obj.text():
                        self.out_dict[inp] = obj.text()

                elif self.dict_inputs[inp][0] in [bool]:
                    # do not add setting if unchanged from default value
                    if self.dict_inputs[inp][1] != obj.isChecked():
                        self.out_dict[inp] = obj.isChecked()

                elif type(self.dict_inputs[inp][0]) == tuple:
                    if str(self.dict_inputs[inp][1]) != obj.currentText():
                        self.out_dict[inp] = obj.currentText()
                else:
                    if str(self.dict_inputs[inp][1]) != obj.text():
                        self.out_dict[inp] = obj.text()
        self.accept()
