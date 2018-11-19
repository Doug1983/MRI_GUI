"""Main.py: Loads and configures the main window for the MRI GUI application."""

__author__ = "Guillaume Doucet"

import sys
import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from subprocess import run, PIPE, Popen

from BaseWidget import BaseWidget

from PyQt5.QtWidgets import *

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPicture
from PyQt5.QtGui import qRgb
from time import clock

class module1(QMainWindow):

    def __init__(self):
        super().__init__()
        #Window creation ==================================================================
        self.setWindowTitle("MRI_GUI")
        #GUI layout =======================================================================
        #Base widget is the parent of each sub-widget within the GUI, it holds the files info
        self.baseWidget = addQWidget(self)

        #Show Main Window 
        self.setCentralWidget(self.baseWidget)
        self.resize(800,600)
        
        self.show()
        self.testEddy()
    
    def testEddy(self):
        #EDDY test
        print(clock())
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        #test = run('bash.exe fsl5.0-eddy_correct /mnt/d/ep2ddiffmddwISO15mm.nii /mnt/d/data 0', stdout=PIPE, stderr=PIPE)
        #QApplication.restoreOverrideCursor()
        #print(clock())
        
        #print(test.stdout)
        #print(test.stderr)

    #Menu methods
class addQWidget(QWidget):
    def __init__(self, parent):
                
        super().__init__(parent)
        self.Label = QLabel(self)
        self.Label.setGeometry(0,0,800,600)
        
        #DISPLAY TEST
        #self.pixCor.setPixmap(QPixmap("cor.jpg"))
        #self.Label.setStyleSheet("QLabel {background-color : black}")
        #spaceBox = QMessageBox()
        #spaceBox.setIcon(QMessageBox.Critical)
        #spaceBox.setText("Eddy current correction script does not accept white spaces. Some were found in your directories.")
        #spaceBox.setInformativeText("To remove white spaces you can: \n 1: Automatically create and delete a temporary folder \n 2: Cancel and manually edit your folder names to remove spaces.")
        #spaceBox.setWindowTitle("White space warning")
        #spaceBox.setStandardButtons(QMessageBox.Cancel)
        #boxAnswer = spaceBox.exec_()
        outProces = Popen('bash')
        outProcess.write('eddy_correct')
        print(outProcess.read())

        #img = nib.load('D:\Sachs Lab\MRI_GUI\ExampleFiles\woody\DCM2Nii\woody_MPRAGE_ADNI_iPAT2_0.6mm_Axials_20120808153048_4.nii.gz')
        #img = nib.load('D:\Sachs Lab\MRI_GUI\ExampleFiles\ep2ddiffmddwISO15MM.nii')
        #print(nib.aff2axcodes(img.affine))
        #img = nib.as_closest_canonical(img)
        
        #print(nib.aff2axcodes(img.affine))
        
        #img_data = img.get_data()
        
        #tempData = img_data[:,:,35].T   
        
        #height, width = tempData.shape
        
        #img_8bit = np.uint8(tempData / np.amax(tempData) * 255)
        #img = QPixmap.fromImage(QImage(img_8bit, width, height, QImage.Format_Grayscale8))
        #self.Label.setPixmap(img.scaled(400,600, Qt.KeepAspectRatio))


if __name__ == '__main__':
    qapp = QApplication(sys.argv) #application object / sys.argv are command line arguments. 
    aw = module1() # basic widget creation, if no parent: widget == window
    
    qapp.exec() #makes sure we have a clean exit
  
