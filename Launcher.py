import os
import sys
import docker

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("dti_launcher")
        self.main_layout = MainLayout(self)
        self.setCentralWidget(self.main_layout)
        self.setGeometry(100, 100, 500, 500)
        self.show()


class MainLayout(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.volumes = dict()

        layout = QVBoxLayout(self)

        # X Server IP
        lbl_ip = QLabel(self)
        lbl_ip.setText("X-Server IP address")
        layout.addWidget(lbl_ip)

        ip_layout = QHBoxLayout(self)
        self.txt_ip_1 = self.add_text_ip("172", 3)
        ip_layout.addWidget(self.txt_ip_1)
        ip_layout.addWidget(QLabel(".", self))

        self.txt_ip_2 = self.add_text_ip("20", 3)
        ip_layout.addWidget(self.txt_ip_2)
        ip_layout.addWidget(QLabel(".", self))

        self.txt_ip_3 = self.add_text_ip("140", 3)
        ip_layout.addWidget(self.txt_ip_3)
        ip_layout.addWidget(QLabel(".", self))

        self.txt_ip_4 = self.add_text_ip("113", 3)
        ip_layout.addWidget(self.txt_ip_4)
        ip_layout.addWidget(QLabel(":", self))

        self.txt_ip_5 = self.add_text_ip("0", 4)
        ip_layout.addWidget(self.txt_ip_5)
        ip_layout.addWidget(QLabel(".", self))

        self.txt_ip_6 = self.add_text_ip("0", 4)
        ip_layout.addWidget(self.txt_ip_6)

        ip_layout.addStretch()

        layout.addLayout(ip_layout)

        # volume mapping
        layout.addStretch()
        layout.addWidget(QLabel("Volume mapping", self))

        host_layout = QHBoxLayout(self)

        host_layout.addWidget(QLabel("Host:    ", self))

        self.txt_host = QLineEdit("", self)
        self.txt_host.setReadOnly(True)
        host_layout.addWidget(self.txt_host)

        self.btn_get_folder = QPushButton(self)
        self.btn_get_folder.setText("Get")
        self.btn_get_folder.clicked.connect(self.get_folder)
        host_layout.addWidget(self.btn_get_folder)

        layout.addLayout(host_layout)

        docker_layout = QHBoxLayout(self)
        docker_layout.addWidget(QLabel("Docker: ", self))
        self.txt_docker = QLineEdit("/mnt/data", self)
        self.txt_docker.setReadOnly(True)
        docker_layout.addWidget(self.txt_docker)

        layout.addLayout(docker_layout)

        self.btn_add = QPushButton(self)
        self.btn_add.setText("Add")
        self.btn_add.clicked.connect(self.add_folder)
        layout.addWidget(self.btn_add)

        self.btn_rem = QPushButton(self)
        self.btn_rem.setText("Remove")
        self.btn_rem.clicked.connect(self.rem_folder)
        layout.addWidget(self.btn_rem)

        self.list_volumes = QListWidget(self)

        layout.addWidget(self.list_volumes)
        lbl_list = QLabel("data folder on host computer || data folder in the docker container")
        lbl_list.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_list)

        # Launch Button
        self.btn_launch = QPushButton(self)
        self.btn_launch.setText("Launch")
        self.btn_launch.clicked.connect(self.launch)

        layout.addStretch()
        layout.addWidget(self.btn_launch)

        self.setLayout(layout)

    def add_text_ip(self, string, max_length):
        txt_ip = QLineEdit(string, self)
        txt_ip.setMaxLength(max_length)
        txt_ip.setFixedWidth(40)
        txt_ip.setAlignment(Qt.AlignCenter)
        return txt_ip

    def get_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setWindowTitle("Select data directory")
        if dlg.exec_():
            files = dlg.selectedFiles()
            if self.validate_host_dir(files[0]):
                self.txt_host.setText(files[0])

    @staticmethod
    def validate_host_dir(directory):
        if os.path.isdir(directory):
            return True
        else:
            return False

    def add_folder(self):
        if self.validate_host_dir(self.txt_host.text()):
            item = QListWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            if self.txt_docker.text()[0] != "/":
                self.txt_docker.setText("/" + self.txt_docker.text())
            item.setText(self.txt_host.text() + "  ||  " + self.txt_docker.text())
            self.list_volumes.addItem(item)
            self.txt_host.setText("")
            self.txt_host.setReadOnly(False)
            self.txt_docker.setText("")
            self.txt_docker.setReadOnly(False)

    def rem_folder(self):
        for item in self.list_volumes.selectedItems():
            self.list_volumes.takeItem(self.list_volumes.row(item))
            if self.list_volumes.count() == 0:
                self.txt_docker.setText("/mnt/data")
                self.txt_docker.setReadOnly(True)

    def launch(self):
        display_env = ["DISPLAY=" + self.txt_ip_1.text() + "."
                       + self.txt_ip_2.text() + "." + self.txt_ip_3.text() + "."
                       + self.txt_ip_4.text() + ":"
                       + self.txt_ip_5.text() + "." + self.txt_ip_6.text(), 'USER=neuro']

        volumes = dict()
        for count in range(self.list_volumes.count()):
            str_split = self.list_volumes.item(count).text().split("  ||  ")
            volumes[str_split[0]] = {'bind': str_split[1], 'mode': 'rw'}

        # add Scripts folder
        curr_path = os.path.abspath(__file__)
        volumes[os.path.split(curr_path)[0]] = {'bind': '/mnt/scripts/', 'mode': 'rw'}

        # docker client
        client = docker.from_env()
        ctnr = client.containers.run(image='sachslab/dti_base:0.3f', environment=display_env,
                                     command='python /mnt/scripts/Main/Main.py', detach=True, tty=True,
                                     volumes=volumes, remove=True)
        # Closing launcher window
        self.parent().close()


if __name__ == '__main__':
    qapp = QApplication(sys.argv)  # application object / sys.argv are command line arguments.
    aw = Launcher()  # basic widget creation, if no parent: widget == window

    qapp.exec()  # makes sure we have a clean exit
