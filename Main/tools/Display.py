import numpy as np
import nibabel as nib
import time

from PyQt5.QtWidgets import QSlider, QLabel, QTextEdit, QHBoxLayout, QVBoxLayout, QSpinBox, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QTransform, QPainter, QColor
from PyQt5.QtCore import Qt, QThread, QSize
from PyQt5 import QtCore

from tools.BaseInterface import *


class VolumeThread(QThread):
    updateVolumeThread = QtCore.pyqtSignal()  # connects to Display

    def __init__(self, parent):
        super().__init__(parent)
        self.shouldRun = False
        self.parentWidget = parent

    def run(self):
        self.shouldRun = True
        while self.shouldRun:
            time.sleep(1/24)  # 24 fps
            self.updateVolumeThread.emit()


class Display(BaseInterface):

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent, dir_dic, bids)

        self.currImg = None
        self.currImg_data = None
        self.contrast = 0
        self.brightness = 0
        self.max_val = 1

        self.init_ui()
        # used to prevent display updates during file maintenance; Since most QtWidgets are triggered on value changed
        # they trigger their callbacks when we programmatically change their value.
        # need to prevent this when updating the GUI
        self.skipDisplayUpdate = True  # Default to true as no files are loaded by default

        # display thread for cycling through the volumes
    def init_thread(self):
        self.volThread = VolumeThread(self)
        self.volThread.updateVolumeThread.connect(self.increment_volume)

    def init_ui(self):
        # Final layout
        self.b4 = QVBoxLayout(self)
        self.setLayout(self.b4)
        
        # file navigator
        b1 = QHBoxLayout()

        self.spinVolume = QSpinBox(self)
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(100)
        self.spinVolume.setValue(0)
        self.spinVolume.valueChanged.connect(self.update_MRI_display)

        self.btnMovie = QPushButton(self)
        self.btnMovie.setText("Auto Cycle")
        self.btnMovie.setCheckable(True)
        self.btnMovie.clicked.connect(self.cycle_volumes)
        b1.addWidget(QLabel("Volume: "))
        b1.addWidget(self.spinVolume)
        b1.addWidget(self.btnMovie)

        # first row
        b12 = QHBoxLayout()
        b12.addLayout(b1, 3)
        
        # Navigation sliders
        b2 = QVBoxLayout()
        b2.addStretch()
        self.slidSagLab = QLabel("Sagital")
        self.slidSagLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidSagLab)
        self.slidSag = ImgSlider(Qt.Horizontal)
        self.slidSag.valueChanged.connect(self.update_MRI_display)
        b2.addWidget(self.slidSag)
        b2.addStretch()

        self.slidCorLab = QLabel("Coronal")
        self.slidCorLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidCorLab)
        self.slidCor = ImgSlider(Qt.Horizontal)
        self.slidCor.valueChanged.connect(self.update_MRI_display)
        b2.addWidget(self.slidCor)
        b2.addStretch()

        self.slidTranLab = QLabel("Transverse")
        self.slidTranLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidTranLab)
        self.slidTran = ImgSlider(Qt.Horizontal)
        self.slidTran.valueChanged.connect(self.update_MRI_display)
        b2.addWidget(self.slidTran)
        b2.addStretch()

        b12.addStretch(1)
        b12.addLayout(b2, 5)
        b12.addStretch(1)
        
        # Sagital, coronal and transverse Plots
        b3 = QHBoxLayout()
        self.pixSag = ImgLabel(self.slidSag, ['slid', 'x', 'y'])
        self.pixSag.mouse_update.connect(self.mouse_update)
        b3.addWidget(self.pixSag, 5)

        self.pixCor = ImgLabel(self.slidCor, ['x', 'slid', 'y'])
        self.pixCor.mouse_update.connect(self.mouse_update)
        b3.addWidget(self.pixCor, 5)

        self.pixTran = ImgLabel(self.slidTran, ['x', 'y', 'slid'])
        self.pixTran.mouse_update.connect(self.mouse_update)
        b3.addWidget(self.pixTran, 5)

        # contrast slider
        bri_con_reset = QVBoxLayout()
        bri_con = QHBoxLayout()
        self.slid_con = QSlider(Qt.Vertical, self)
        self.slid_con.setMinimum(-255)
        self.slid_con.setMaximum(255)
        self.slid_con.setValue(0)
        self.slid_con.valueChanged.connect(self.update_contrast)
        bri_con.addWidget(self.slid_con)

        # brightness slider
        self.slid_bri = QSlider(Qt.Vertical, self)
        self.slid_bri.setMinimum(-255)
        self.slid_bri.setMaximum(255)
        self.slid_bri.setValue(0)
        self.slid_bri.valueChanged.connect(self.update_contrast)
        bri_con.addWidget(self.slid_bri)
        bri_con_reset.addLayout(bri_con)

        btn_reset = QPushButton('Reset')
        btn_reset.clicked.connect(self.reset_bri_con)
        bri_con_reset.addWidget(btn_reset)

        b3.addLayout(bri_con_reset, 1)

        # Log text field
        self.b4.addLayout(b12, 1)
        self.b4.addStretch()
        lblMRI = QLabel("MRI View")
        lblMRI.setAlignment(Qt.AlignCenter)
        self.b4.addWidget(lblMRI)
        self.b4.addLayout(b3,5)
        self.b4.addStretch()
        self.logField = QTextEdit(self)
        lblLog = QLabel("Log File View")
        lblLog.setAlignment(Qt.AlignCenter)
        self.b4.addWidget(lblLog)
        self.b4.addWidget(self.logField, 1)

    def reset_bri_con(self):
        self.slid_bri.setValue(0)
        self.slid_con.setValue(0)
        self.update_MRI_display()

    def update_file_selection(self, files, _):

        if len(files['file_names']) > 0:
            curr_file = files['file_names'][0]

            if curr_file != "None":
                self.skipDisplayUpdate = True
                self.currImg = nib.load(curr_file)

                # convert image to approximate canonical coordinates
                self.currImg = nib.as_closest_canonical(self.currImg)
                self.currImg_data = self.currImg.get_data()
                self.max_val = np.amax(self.currImg_data)
                # get the image size: (X,Y,Z,Volumes)

                self.nDims = self.currImg.header.get_data_shape()
                # update sliders according to each dimension

                # to fix a crash when changing across files with different dimensions where it sets
                # the maximum value lower than the current value, we set the values at 0 before changing the max
                self.slidSag.setValue(0)
                self.slidCor.setValue(0)
                self.slidTran.setValue(0)
                self.slid_con.setValue(0)

                self.slidSag.setMaximum(self.nDims[0]-1)
                self.slidCor.setMaximum(self.nDims[1]-1)
                self.slidTran.setMaximum(self.nDims[2]-1)
                # self.slid_con.setMaximum(self.max_val*2)

                # self.slid_bri.setMaximum(self.max_val)
                # self.slid_bri.setMinimum(-self.max_val)

                # if we have volume data
                if len(self.nDims) > 3:
                    self.spinVolume.setMaximum(self.nDims[3]-1)
                else:
                    self.spinVolume.setMaximum(0)

                self.slidSag.setValue(self.currImg_data.shape[0]/2)
                self.slidCor.setValue(self.currImg_data.shape[1]/2)
                self.slidTran.setValue(self.currImg_data.shape[2]/2)
                # self.slid_con.setValue(self.max_val)
                self.slid_con.setValue(0)
                self.slid_bri.setValue(0)

                self.spinVolume.setValue(0)

                self.skipDisplayUpdate = False

                self.update_MRI_display()

        else:
            self.currImg_data = None
            self.update_MRI_display()

    def update_contrast(self):
        if not self.skipDisplayUpdate:
            # current contrast
            self.contrast = self.slid_con.value()
            self.brightness = self.slid_bri.value()
            self.update_MRI_display()

    def cycle_volumes(self):
        if self.btnMovie.isChecked():
            self.init_thread()
            # print('starting thread')
            # self.volThread.shouldRun = True
            self.volThread.start()
        else:
            # print('stopping thread')
            if self.volThread.isRunning():
                self.volThread.shouldRun = False

    @QtCore.pyqtSlot(list)
    def mouse_update(self, positions):
        # positions returns the position in voxels
        # convert to patient space
        if self.currImg is not None:
            M = self.currImg.affine[:3, :3]
            abc = self.currImg.affine[:3, 3]
            patient_space_position = M.dot(positions) + abc

            self.logField.setText('Voxel positions: ' + str(positions) + '\n' + 'Patient Space positions: [' +
                                  '{0:5.2f}'.format(patient_space_position[0]) + ', ' +
                                  '{0:5.2f}'.format(patient_space_position[1]) + ', ' +
                                  '{0:5.2f}'.format(patient_space_position[2]) + ']')

    @QtCore.pyqtSlot()
    def increment_volume(self):
        if self.spinVolume.value() == self.spinVolume.maximum():
            self.spinVolume.setValue(0)
        else:
            self.spinVolume.setValue(self.spinVolume.value() + 1)
        self.update_MRI_display()

    def update_MRI_display(self):
        if not self.skipDisplayUpdate:
            if self.currImg_data is not None:
                # get sliders positions
                sagPos = round(self.slidSag.value())
                corPos = round(self.slidCor.value())
                tranPos = round(self.slidTran.value())
                volPos = self.spinVolume.value()

                if len(self.nDims) > 3:
                    tempDataSag = self.currImg_data[sagPos, :, :, volPos].T
                    tempDataCor = self.currImg_data[:, corPos, :, volPos].T
                    tempDataTran = self.currImg_data[:, :, tranPos, volPos].T
                    height, width, depth, volume = self.currImg_data.shape
                else:
                    tempDataSag = self.currImg_data[sagPos, :, :].T
                    tempDataCor = self.currImg_data[:, corPos, :].T
                    tempDataTran = self.currImg_data[:, :, tranPos].T
                    height, width, depth = self.currImg_data.shape
            
                # get the label Geometry
                pixSagGeom = self.pixSag.geometry()
                pixCorGeom = self.pixCor.geometry()
                pixTranGeom = self.pixTran.geometry()
            
                # QPixmap only accepts 8bits greyscale values so we need to normalize the data
                # and bring back to 8 bit data
                # tempDataSag = np.uint8(np.clip(tempDataSag, 0, self.maxVal) / self.maxVal * 255)
                # tempDataCor = np.uint8(np.clip(tempDataCor, 0, self.maxVal) / self.maxVal * 255)
                # tempDataTran = np.uint8(np.clip(tempDataTran, 0, self.maxVal) / self.maxVal * 255)

                # contrast

                tempDataSag = self.update_brightness_contrast(tempDataSag / self.max_val * 255, self.brightness,
                                                              self.contrast)
                tempDataCor = self.update_brightness_contrast(tempDataCor / self.max_val * 255, self.brightness,
                                                              self.contrast)
                tempDataTran = self.update_brightness_contrast(tempDataTran / self.max_val * 255, self.brightness,
                                                               self.contrast)

                bytes_per_line = tempDataSag.nbytes / tempDataSag.shape[0]
                tempDataSag = QPixmap.fromImage(QImage(bytes(tempDataSag), width, depth, bytes_per_line,
                                                       QImage.Format_Grayscale8))
                tempDataSag = tempDataSag.transformed(QTransform().scale(1, -1))

                bytes_per_line = tempDataCor.nbytes / tempDataCor.shape[0]
                tempDataCor = QPixmap.fromImage(QImage(bytes(tempDataCor), height, depth, bytes_per_line,
                                                       QImage.Format_Grayscale8))
                tempDataCor = tempDataCor.transformed(QTransform().scale(1, -1))

                bytes_per_line = tempDataTran.nbytes / tempDataTran.shape[0]
                tempDataTran = QPixmap.fromImage(QImage(bytes(tempDataTran), height, width, bytes_per_line,
                                                        QImage.Format_Grayscale8))

                # self.pixSag.setPixmap(tempDataSag.scaled(pixSagGeom.width(), pixSagGeom.height(), Qt.KeepAspectRatio))
                # self.pixCor.setPixmap(tempDataCor.scaled(pixCorGeom.width(), pixCorGeom.height(), Qt.KeepAspectRatio))
                # self.pixTran.setPixmap(tempDataTran.scaled(pixTranGeom.width(), pixTranGeom.height(), Qt.KeepAspectRatio))

                self.pixSag.set_pixmap(tempDataSag, [sagPos, corPos, tranPos])
                self.pixCor.set_pixmap(tempDataCor, [sagPos, corPos, tranPos])
                self.pixTran.set_pixmap(tempDataTran, [sagPos, corPos, tranPos])

            else:  # clear
                self.pixSag.clear()
                self.pixCor.clear()
                self.pixTran.clear()

    @staticmethod
    def update_brightness_contrast(color, brightness, contrast):
        factor = (259 * (contrast + 255)) / (255 * (259 - contrast))

        out_color = np.uint8(np.clip(factor * (color + brightness - 128) + 128, 0, 255))

        return out_color


class ImgSlider(QSlider):
    def __init__(self, align):
        super().__init__(align)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(50)

    def increment_value(self, increment):
        self.setValue(int(self.value() + increment))


class ImgLabel(QLabel):
    mouse_update = QtCore.pyqtSignal(list)

    def __init__(self, linked_slider, order):
        super().__init__()
        self.setMouseTracking(True)
        self.linked_slider = linked_slider
        self.order = order
        self.setStyleSheet("QLabel {background-color : black}")
        self.img_size = QSize()
        self.sliders = list()
        self.slice_colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255)]
        self.mouse_pos_x = 0
        self.mouse_pos_y = 0

    def wheelEvent(self, event):

        # 120 units = 15 degrees = 1 step in the slider
        self.linked_slider.increment_value(event.angleDelta().y() / 120)

    def mouseMoveEvent(self, event):
        # getting mouse position in QLabel space, need to normalize to convert to pixel space
        out_position = list()

        self.mouse_pos_x = event.pos().x() / self.rect().width()
        self.mouse_pos_y = event.pos().y() / self.rect().height()

        for order in self.order:
            if order == 'slid':
                out_position.append(self.linked_slider.value())
            elif order == 'x':
                out_position.append(round(self.mouse_pos_x * self.img_size.width()))
            elif order == 'y':
                out_position.append(round(self.mouse_pos_y * self.img_size.height()))

        self.mouse_update.emit(out_position)

    def paintEvent(self, event):
        paint = QPainter(self)
        paint.setPen(QColor(255, 0, 0))

        if self.pixmap() is not None:
            paint.drawPixmap(self.rect(), self.pixmap())

            # draw slice markers for other orientations
            # x-axis
            i = self.order.index('x')
            curr_color = self.slice_colors[i]
            curr_x = round(self.sliders[i] / self.img_size.width() * self.width())
            paint.setPen(curr_color)
            # paint.drawLine(curr_x, 0, curr_x, self.height())
            paint.drawLine(curr_x, 0, curr_x, 20)
            paint.drawLine(curr_x, self.height()-20, curr_x, self.height())

            # y axis
            i = self.order.index('y')
            curr_color = self.slice_colors[i]
            # transverse plane
            if i == 2:
                curr_y = self.height() - round(self.sliders[i] / self.img_size.height() * self.height())
            else:
                curr_y = round(self.sliders[i] / self.img_size.height() * self.height())
            paint.setPen(curr_color)
            paint.drawLine(0, curr_y, 20, curr_y)
            paint.drawLine(self.width()-20, curr_y, self.width(), curr_y)

        # paint.drawText(self.mouse_pos_x + 10, self.mouse_pos_y + 10, str(self.mouse_pos_y))
        # paint.drawLine(0, 0, self.mouse_pos_x, self.mouse_pos_y)

    def set_pixmap(self, pixmap, sliders):

        self.img_size = pixmap.size()
        self.sliders = sliders
        super().setPixmap(pixmap)
