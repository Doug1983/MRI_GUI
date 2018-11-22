import os
import numpy as np
import nibabel as nib
import time

from PyQt5.QtWidgets import QWidget, QSlider, QLabel, QTextEdit, QHBoxLayout, QVBoxLayout, \
    QListWidget, QSpinBox, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QTransform, QFont
from PyQt5.QtCore import Qt, QThread
from PyQt5 import QtCore


class VolumeThread(QThread):
    updateVolumeThread = QtCore.pyqtSignal()  # connects to Display

    def __init__(self, parent):
        super().__init__(parent)
        self.shouldRun = True
        self.parentWidget = parent

    def run(self):
        while self.shouldRun:
            time.sleep(1/24)  # 24 fps
            self.updateVolumeThread.emit()
        self.quit()

    def stop(self):
        self.shouldRun = False


class Display(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parentWidget = parent
        self.baseDir = ''
        self.allNii = []
        self.logFile = ''
        self.init_ui()
        self.currImg = None
        self.currImg_data = None
        self.maxVal = 1
        self.initThread()
        # used to prevent display updates during file maintenance; Since most QtWidgets are triggered on value changed
        # they trigger their callbacks when we programmatically change their value.
        # need to prevent this when updating the GUI
        self.skipDisplayUpdate = True  # Default to true as no files are loaded by default

        # display thread for cycling through the volumes
    def initThread(self):
        self.volThread = VolumeThread(self)
        self.volThread.updateVolumeThread.connect(self.incrementVolume)

    def init_ui(self):
        # Final layout
        self.b4 = QVBoxLayout(self)
        self.setLayout(self.b4)
        
        # file navigator
        b1 = QVBoxLayout()
        b1.addStretch()
        self.fileNavLab = QLabel("Display file:")
        self.fileNavLab.setAlignment(Qt.AlignCenter)
        b1.addWidget(self.fileNavLab)
        self.fileNav = QListWidget(self)
        self.fileNav.addItem("None"); 
        self.fileNav.setCurrentRow(0)
        self.fileNav.setFont(QFont("times", 12))
        # self.fileNav.setCurrentIndex(0)
        self.fileNav.itemClicked.connect(self.updateSelectedFile)
        b1.addWidget(self.fileNav)

        b2 = QHBoxLayout()
        self.spinVolume = QSpinBox(self)
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(100)
        self.spinVolume.setValue(0)
        self.spinVolume.valueChanged.connect(self.updateMRIDisplay)

        self.btnMovie = QPushButton(self)
        self.btnMovie.setText("Auto Cycle")
        self.btnMovie.setCheckable(True)
        self.btnMovie.clicked.connect(self.cycleVolumes)
        b1.addWidget(QLabel("Volume: "))
        b2.addWidget(self.spinVolume)
        b2.addWidget(self.btnMovie)

        b1.addLayout(b2)
        b1.addStretch()

        # first row
        b12 = QHBoxLayout()
        b12.addLayout(b1, 3)
        
        # Navigation sliders
        b2 = QVBoxLayout()
        b2.addStretch()
        self.slidSagLab = QLabel("Sagital")
        self.slidSagLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidSagLab)
        self.slidSag = QSlider(Qt.Horizontal)
        self.slidSag.setMinimum(0)
        self.slidSag.setMaximum(100)
        self.slidSag.setValue(50)
        self.slidSag.valueChanged.connect(self.updateMRIDisplay)
        b2.addWidget(self.slidSag)
        b2.addStretch()

        self.slidCorLab = QLabel("Coronal")
        self.slidCorLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidCorLab)
        self.slidCor = QSlider(Qt.Horizontal)
        self.slidCor.setMinimum(0)
        self.slidCor.setMaximum(100)
        self.slidCor.setValue(50)
        self.slidCor.valueChanged.connect(self.updateMRIDisplay)
        b2.addWidget(self.slidCor)
        b2.addStretch()

        self.slidTranLab = QLabel("Transverse")
        self.slidTranLab.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.slidTranLab)
        self.slidTran = QSlider(Qt.Horizontal)
        self.slidTran.setMinimum(0)
        self.slidTran.setMaximum(100)
        self.slidTran.setValue(50)
        self.slidTran.valueChanged.connect(self.updateMRIDisplay)
        b2.addWidget(self.slidTran)
        b2.addStretch()

        b12.addStretch(1)
        b12.addLayout(b2, 5)
        b12.addStretch(1)
        
        # Sagital, coronal and transverse Plots
        b3 = QHBoxLayout()
        self.pixSag = QLabel(self)
        self.pixSag.setStyleSheet("QLabel {background-color : black}")
        b3.addWidget(self.pixSag)

        self.pixCor = QLabel(self)
        self.pixCor.setStyleSheet("QLabel {background-color : black}")
        b3.addWidget(self.pixCor)

        self.pixTran = QLabel(self)
        self.pixTran.setStyleSheet("QLabel {background-color : black}")
        b3.addWidget(self.pixTran)


        # contrast slider
        self.slidCon = QSlider( Qt.Vertical, self)
        self.slidCon.setMinimum(1)
        self.slidCon.setMaximum(255)
        self.slidCon.setValue(128)
        self.slidCon.valueChanged.connect(self.updateContrast)
        b3.addWidget(self.slidCon)

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

    def updateSelectedFile(self):
        currFile = self.fileNav.currentItem().text()
        currID = self.fileNav.currentRow()
        
        if currFile != "None" and currID != -1:
            self.skipDisplayUpdate = True
            self.currImg = nib.load(os.path.join(self.baseDir, currFile))

            # convert image to approximate canonical coordinates
            self.currImg = nib.as_closest_canonical(self.currImg)
            self.currImg_data = self.currImg.get_data()
            self.maxVal = np.amax(self.currImg_data)
            # get the image size: (X,Y,Z,Volumes)

            self.nDims = self.currImg.header.get_data_shape()
            # update sliders according to each dimension

            # to fix a crash when changing across files with different dimensions where it sets
            # the maximum value lower than the current value, we set the values at 0 before changing the max
            self.slidSag.setValue(0)
            self.slidCor.setValue(0)
            self.slidTran.setValue(0)
            self.slidCon.setValue(1)

            self.slidSag.setMaximum(self.nDims[0]-1)
            self.slidCor.setMaximum(self.nDims[1]-1)
            self.slidTran.setMaximum(self.nDims[2]-1)
            self.slidCon.setMaximum(self.maxVal*2)

            #fif we have volume data
            if len(self.nDims) > 3:
                self.spinVolume.setMaximum(self.nDims[3]-1)
            else:
                self.spinVolume.setMaximum(0)

            self.slidSag.setValue(self.currImg_data.shape[0]/2)
            self.slidCor.setValue(self.currImg_data.shape[1]/2)
            self.slidTran.setValue(self.currImg_data.shape[2]/2)
            self.slidCon.setValue(self.maxVal)

            self.spinVolume.setValue(0)

            self.skipDisplayUpdate = False

            self.updateMRIDisplay()

        elif currFile == "None":
            self.currImg_data = None
            self.updateMRIDisplay()

    def updateContrast(self):
        if not self.skipDisplayUpdate:
            #curr contrast
            self.maxVal = self.slidCon.value()
            self.updateMRIDisplay()

    def cycleVolumes(self):
        if self.btnMovie.isChecked():
            print('starting thread')
            self.volThread.shouldRun = True
            self.volThread.start()
        else:
            print('stopping thread')
            self.volThread.shouldRun = False
    
    @QtCore.pyqtSlot()
    def incrementVolume(self):
        if self.spinVolume.value() == self.spinVolume.maximum():
            self.spinVolume.setValue(0)
        else:
            self.spinVolume.setValue(self.spinVolume.value() + 1)
        self.updateMRIDisplay()

    def updateMRIDisplay(self):
        if not self.skipDisplayUpdate:
            if self.currImg_data is not None:
                # get sliders positions
                sagPos = round(self.slidSag.value())
                corPos = round(self.slidCor.value())
                tranPos = round(self.slidTran.value())
                volPos = self.spinVolume.value()

                if (len(self.nDims)> 3):
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
                tempDataSag = np.uint8(np.clip(tempDataSag, 0, self.maxVal) / self.maxVal * 255)
                tempDataCor = np.uint8(np.clip(tempDataCor, 0, self.maxVal) / self.maxVal * 255)
                tempDataTran = np.uint8(np.clip(tempDataTran, 0, self.maxVal) / self.maxVal * 255)

                bytes_per_line = tempDataSag.nbytes / tempDataSag.shape[0]
                tempDataSag = QPixmap.fromImage(QImage(bytes(tempDataSag), width, depth, bytes_per_line, QImage.Format_Grayscale8))
                tempDataSag = tempDataSag.transformed(QTransform().scale(1, -1))

                bytes_per_line = tempDataCor.nbytes / tempDataCor.shape[0]
                tempDataCor = QPixmap.fromImage(QImage(bytes(tempDataCor), height, depth, bytes_per_line, QImage.Format_Grayscale8))
                tempDataCor = tempDataCor.transformed(QTransform().scale(1, -1))

                bytes_per_line = tempDataTran.nbytes / tempDataTran.shape[0]
                tempDataTran = QPixmap.fromImage(QImage(bytes(tempDataTran), height, width, bytes_per_line, QImage.Format_Grayscale8))

                self.pixSag.setPixmap(tempDataSag.scaled(pixSagGeom.width(), pixSagGeom.height(), Qt.KeepAspectRatio))
                self.pixCor.setPixmap(tempDataCor.scaled(pixCorGeom.width(), pixCorGeom.height(), Qt.KeepAspectRatio))
                self.pixTran.setPixmap(tempDataTran.scaled(pixTranGeom.width(), pixTranGeom.height(), Qt.KeepAspectRatio))

            else:  # clear
                self.pixSag.clear()
                self.pixCor.clear()
                self.pixTran.clear()


    @QtCore.pyqtSlot(list, str, str)
    def postProcessUpdate(self, allNii, logFile, baseDir):
        self.baseDir = baseDir
        self.allNii = allNii
        self.logFile = logFile

        self.updatelogdisplay()
        self.updateFileNavigator()

    def updatelogdisplay(self):
        self.logField.setText(self.logFile)


    def updateFileNavigator(self):  
        self.fileNav.clear()
        self.fileNav.addItem("None")
        for File in self.allNii:
            self.fileNav.addItem(File)
        
        #self.fileNav.clear()
        #for File, Nbr in allDICOM.items():
        #     self.fileNav.addItem(File + "[" + str(Nbr[0]) + ":"+ str(Nbr[1]) +"].dcm")
