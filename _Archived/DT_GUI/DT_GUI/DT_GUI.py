import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QMessageBox, QMainWindow, QFileDialog

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon

class DTI_MAIN(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #Window creation
        self.setGeometry(150,100, 600, 700) #X,Y,width,height
        self.setWindowTitle("DT_GUI")
        self.setWindowIcon(QIcon('brain.png'))
        self.statusBar().showMessage('ready')

        #Buttons
        loadBtn = QPushButton('Load Data', self)
        loadBtn.clicked.connect(self.loadButtonClick)
        loadBtn.setGeometry(10, 100, 100, 50)


        quitBtn = QPushButton('Quit', self)
        quitBtn.clicked.connect(self.quitButtonClick)
        quitBtn.setGeometry(10, 550, 100, 50)
                
        #Display window
        self.show()


    #Button methods
    def loadButtonClick(self):
        fname = QFileDialog.getOpenFileName(self, 'Open File', '/home', 'Text Files(*.txt)')

        if fname[0]:
            print(fname[0])


    def quitButtonClick(self):
        self.close()

    

    #Main Window events
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm', "Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) # self, window title, Message, choices, default option

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        
if __name__ == '__main__':
    qapp = QApplication(sys.argv) #application object / sys.argv are command line arguments. 
    aw = DTI_MAIN() # basic widget creation, if no parent: widget == window
    #timer = QTimer()

    qapp.exec() #makes sure we have a clean exit
  