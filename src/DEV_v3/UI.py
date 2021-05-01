import numpy as np
import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from datetime import datetime

import board
import Adafruit_ADS1x15 as adc
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


app = QApplication(sys.argv)

class MOS:
    def __init__(self, adc, channel):
        super(MOS, self).__init__()
        self.GAIN = 2 / 3
        self.adc = adc
        self.channel = channel

    def read(self):
        return (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144


class graph(pg.PlotWidget):
    def __init__(self):
        super(graph, self).__init__()
        self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")


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

    def expose(self):
        self.stepDirection = stepper.FORWARD
        print("Exposing")
        self.step(110)

    def recover(self):
        self.stepDirection = stepper.BACKWARD
        self.step(110)
        print("Recovering")

    def moveLeft(self):
        self.stepDirection = stepper.FORWARD
        self.step(2)
        print("<<")

    def moveRight(self):
        self.stepDirection = stepper.BACKWARD
        self.step(2)
        print(">>")

    def zero(self):
        self.currentPos = 0

    def step(self, steps):
        for i in range(steps):
            if self.stepperMinVal < self.currentPos < self.stepperMaxVal:
                QTimer.singleShot(10, lambda: self.motor.onestep(direction=self.stepDirection, style=self.stepStyle))
                if self.stepDirection == stepper.FORWARD:
                    self.currentPos = self.currentPos + 1
                else:
                    self.currentPos = self.currentPos - 1
        self.motor.release()


class MOTOR:
    def __init__(self, channel, name):
        super(MOTOR, self).__init__()
        self.motor = channel
        self.name = name

        self.status = False

    def activate(self):
        self.motor.throttle = 1
        self.status = True
        print("{}: ON".format(self.name))

    def deactivate(self):
        self.motor.throttle = 0
        self.status = False
        print("{}: OFF".format(self.name))

    def toggle(self):
        if self.status:
            self.deactivate()
        else:
            self.activate()


class HomeWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(HomeWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        self.loadWindowSettings()
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        self.loadComponents()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.release()
        print("Components Loaded")

    def HWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Start Test")
        self.b1.clicked.connect(lambda: self.showSTW())

        self.b2 = self.button()
        self.b2.setButtonText("Purge")
        self.b2.clicked.connect(lambda: self.showPW())

        self.b3 = self.button()
        self.b3.setButtonText("Control Panel")
        self.b3.clicked.connect(lambda: self.showCPW())

        self.b4 = self.button()
        self.b4.setButtonText("Sensor Graph")
        self.b4.clicked.connect(lambda: self.showSGW())

        self.b5 = self.button()
        self.b5.setButtonText("Settings")
        self.b5.clicked.connect(lambda: self.showSW())

        self.b6 = self.button()
        self.b6.setButtonText("Exit")
        self.b6.clicked.connect(lambda: QApplication.closeAllWindows())

    def showPW(self):
        self.PW = self.PurgeWindow()
        self.PW.show()
        self.close()

    def showSW(self):
        self.SW = self.SettingsWindow()
        self.SW.show()
        self.close()

    def showSTW(self):
        self.STW = self.StartTestWindow()
        self.STW.show()
        self.close()

    def showCPW(self):
        self.CPW = self.ControlPanelWindow()
        self.CPW.show()
        self.close()

    def showSGW(self):
        self.SGW = self.SensorGraphWindow()
        self.SGW.show()
        self.close()

    def HWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)
        self.layout.addWidget(self.b5)
        self.layout.addWidget(self.b6)

        self.setLayout(self.layout)