import numpy as np
import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from pandas import read_csv as rc
import adminGui
import usrGui
global bg_color
bg_color = '#484848'
w = 320
h = 240

prm_list = rc('parameters.csv', delimiter=',', header='infer')
sVersion = prm_list['Software Version'].values
dVersion = prm_list['Device Version'].values
dID = prm_list['Device ID'].values

cwd = os.getcwd()

class Window(QWidget):
    class usrButton(QPushButton):
        def __init__(self, parent=None):
            super(Window.usrButton, self).__init__()
            self.setText('User GUI')

    class adminButton(QPushButton):
        def __init__(self, parent=None):
            super(Window.adminButton, self).__init__()
            self.setText('Admin GUI')

    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Choose Which UI')
        b1 = self.usrButton()
        b2 = self.adminButton()
        b3 = self.exitButton()
        b1.clicked.connect(lambda: self.userGUI())
        b2.clicked.connect(lambda: self.adminGUI())
        layout.addWidget(label)
        layout.addWidget(b1)
        layout.addWidget(b2)
        layout.addWidget(b3)
        self.setLayout(layout)

    def userGUI(self):
        self.u = usrGui.Window1()
        self.u.show()
        self.close()

    def adminGUI(self):
        os.system('python3 {}/adminGui.py'.format(cwd))

        self.a = adminGui.MainClass()
        self.a.show()
        self.close()


class Splashscreen(QWidget):
    def __init__(self, *args, **kwargs):
        super(Splashscreen, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        img = QLabel()
        pix = QPixmap('hetek_logo.png')
        img.setPixmap(pix.scaledToWidth(w-40))
        # img.resize(w,h)
        # print('w: {} \nh: {}'.format(self.frameGeometry().width(), self.frameGeometry().height()))
        svLbl = QLabel('Software Version: {}'.format(sVersion[-1:1]))
        svLbl.setFont(QFont('Times', 10))
        dvLbl = QLabel('Device Version: {}'.format(dVersion))
        dvLbl.setFont(QFont('Times', 10))
        dIdLbl = QLabel('Device ID: {}'.format(dID))
        dIdLbl.setFont(QFont('Times', 10))
        layout.addWidget(img, 0, 0, 3, 3)
        layout.addWidget(svLbl, 4, 0, 1, 1)
        layout.addWidget(dvLbl, 4, 1, 1, 1)
        layout.addWidget(dIdLbl, 4, 2, 1, 1)
        self.setLayout(layout)
        QTimer.singleShot(3000, lambda: self.window_a())

    def window_a(self):
        self.w = Window()
        self.w.show()
        self.close()


def main():
    app = QApplication(sys.argv)
    win = Splashscreen()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
