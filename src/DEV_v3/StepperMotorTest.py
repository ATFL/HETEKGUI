from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import Adafruit_ADS1x15 as adc
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

import sys

app = QApplication(sys.argv)

class Stepper(QWidget):
    def __init__(self, channel):
        super(Stepper, self).__init__()
        self.motor = channel
        self.currentPos = 0
        self.stepDirection = stepper.FORWARD
        self.stepStyle = stepper.SINGLE
        self.motor.release()
        self.stepperMinVal = -20
        self.stepperMaxVal = 140
        self.stepperPos = "Recover"

    def expose(self):
        if not self.stepperPos == "exposed":
            self.stepDirection = stepper.BACKWARD
            print("Exposing")
            self.step(110)
            self.stepperPos = "exposed"

    def recover(self):
        if not self.stepperPos == "recovered":
            self.stepDirection = stepper.FORWARD
            self.step(110)
            print("Recovering")
            self.stepperPos = "recovered"

    def moveLeft(self):
        self.stepDirection = stepper.BACKWARD
        self.step(10)
        print("<<")
        self.stepperPos = "mid"

    def moveRight(self):
        self.stepDirection = stepper.FORWARD
        self.step(10)
        print(">>")
        self.stepperPos = "mid"

    def zero(self):
        self.currentPos = 0
        self.stepperPos = "recovered"

    def step(self, steps):
        for i in range(steps):
            QTimer.singleShot(10, lambda: self.motor.onestep(direction=self.stepDirection, style=self.stepStyle))
            if self.stepDirection == stepper.FORWARD:
                self.currentPos = self.currentPos + 1
            else:
                self.currentPos = self.currentPos - 1
        self.motor.release()
        
    def move(self):
        self.motor.onestep(direction=self.stepDirection, style=self.stepStyle)
        

class ControlPanelWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(ControlPanelWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(ControlPanelWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.CPWButtonSetup()
        self.CPWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(0x63)
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)

        self.SM.motor.release()

        print("Components Loaded")

    def CPWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Expose")
        self.b1.clicked.connect(lambda: self.SM.expose())

        self.b2 = self.button()
        self.b2.setButtonText("Recover")
        self.b2.clicked.connect(lambda: self.SM.recover())
        
        self.buttonStatus = False
        
        self.b3 = self.button()
        self.b3.setButtonText("<<")
        # self.b3.clicked.connect(lambda: self.SM.moveLeft())
        self.b3.pressed.connect(lambda: self.move("L"))
        self.b3.released.connect(lambda: self.endMove())

        self.b4 = self.button()
        self.b4.setButtonText(">>")
        # self.b4.clicked.connect(lambda: self.SM.moveRight())
        self.b4.pressed.connect(lambda: self.move("R"))
        self.b4.released.connect(lambda: self.endMove())

    def move(self, direction):
        if direction == "L":
            self.SM.direction = stepper.BACKWARD
        else:
            self.SM.direction = stepper.FORWARD
            
        self.buttonStatus = True
        while self.buttonStatus:
            self.SM.move()
        self.SM.motor.release()
    
    def endMove(self):
        self.buttonStatus = False
        
    
    def CPWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)

        self.setLayout(self.layout)

def main():
    UI = ControlPanelWindow()
    UI.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()