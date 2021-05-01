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
        super(HomeWindow, self).__init__()
        self.loadWindowSettings()
        # self.loadComponents()
        self.HWButtonSetup()
        self.HWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
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
        self.PW = PurgeWindow()
        self.PW.show()
        self.close()

    def showSW(self):
        self.SW = SettingsWindow()
        self.SW.show()
        self.close()

    def showSTW(self):
        self.STW = StartTestWindow()
        self.STW.show()
        self.close()

    def showCPW(self):
        self.CPW = ControlPanelWindow()
        self.CPW.show()
        self.close()

    def showSGW(self):
        self.SGW = SensorGraphWindow()
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


class PurgeWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(PurgeWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(PurgeWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.PWButtonSetup()
        self.PWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def PWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Purge")
        self.b1.clicked.connect(lambda: self.purge())

        self.b2 = self.button()
        self.b2.setButtonText("Home")
        self.b2.clicked.connect(lambda: self.showHW())

        self.b3 = self.button()
        self.b3.setButtonText("Control Panel")
        self.b3.clicked.connect(lambda: self.showCPW())

        self.b4 = self.button()
        self.b4.setButtonText("Stop")
        self.b4.clicked.connect(lambda: self.stop())

        self.b5 = self.button()
        self.b5.setButtonText("Start Test")
        self.b5.clicked.connect(lambda: self.showSTW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    def showCPW(self):
        self.CPW = ControlPanelWindow()
        self.CPW.show()
        self.close()

    def showSTW(self):
        self.STW = StartTestWindow()
        self.STW.show()
        self.close()

    def purge(self):
        pass

    def stop(self):
        pass

    def PWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)
        self.layout.addWidget(self.b5)

        self.setLayout(self.layout)


class SettingsWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(SettingsWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(SettingsWindow, self).__init__()
        self.loadWindowSettings()
        # self.loadComponents()
        self.SWButtonSetup()
        self.SWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def SWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Home")
        self.b1.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    def SWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        # self.layout.addWidget(self.b2)
        # self.layout.addWidget(self.b3)
        # self.layout.addWidget(self.b4)

        self.setLayout(self.layout)


class StartTestWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(StartTestWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(StartTestWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.STWButtonSetup()
        self.graphSetup()
        self.STWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()

        print("Components Loaded")

    def graphSetup(self):
        self.sensorGraph = graph()

        self.timeArray = []
        self.sensor1Array = []
        self.sensor2Array = []
        self.sensor3Array = []

        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen='r')
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='g')
        self.sensor3Plot = self.sensorGraph.plot(self.timeArray, self.sensor3Array, pen='b')

    def STWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Start")
        self.b1.clicked.connect(lambda: self.initializeTest())

        self.b2 = self.button()
        self.b2.setButtonText("Stop")
        self.b2.clicked.connect(lambda: self.stop())

        self.b3 = self.button()
        self.b3.setButtonText("Home")
        self.b3.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    def initializeTest(self):
        pass

    def stop(self):
        pass

    def STWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.sensorGraph)

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)

        self.setLayout(self.layout)


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
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()

        print("Components Loaded")

    def CPWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Expose")
        self.b1.clicked.connect(lambda: self.SM.expose())

        self.b2 = self.button()
        self.b2.setButtonText("Recover")
        self.b2.clicked.connect(lambda: self.SM.recover())

        self.b3 = self.button()
        self.b3.setButtonText("<<")
        self.b3.clicked.connect(lambda: self.SM.moveLeft())

        self.b4 = self.button()
        self.b4.setButtonText(">>")
        self.b4.clicked.connect(lambda: self.SM.moveRight())

        self.b5 = self.button()
        self.b5.setButtonText("Toggle Valve")
        self.b5.clicked.connect(lambda: self.valve.toggle())

        self.b6 = self.button()
        self.b6.setButtonText("Toggle Pump")
        self.b6.clicked.connect(lambda: self.pump.toggle())

        self.b7 = self.button()
        self.b7.setButtonText("Zero Stepper Motor")
        self.b7.clicked.connect(lambda: self.SM.zero())

        self.b8 = self.button()
        self.b8.setButtonText("Home")
        self.b8.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    def CPWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)
        self.layout.addWidget(self.b5)
        self.layout.addWidget(self.b6)
        self.layout.addWidget(self.b7)
        self.layout.addWidget(self.b8)

        self.setLayout(self.layout)


class SensorGraphWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(SensorGraphWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(SensorGraphWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.SGWButtonSetup()
        self.graphSetup()
        self.SGWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve")
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def graphSetup(self):
        self.sensorGraph = graph()

        self.timeArray = []
        self.sensor1Array = []
        self.sensor2Array = []
        self.sensor3Array = []

        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen='r')
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='g')
        self.sensor3Plot = self.sensorGraph.plot(self.timeArray, self.sensor3Array, pen='b')
        self.liveGraph()

    def liveGraph(self):
        pass

    def SGWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Expose")
        self.b1.clicked.connect(lambda: self.SM.expose())

        self.b2 = self.button()
        self.b2.setButtonText("Recover")
        self.b2.clicked.connect(lambda: self.SM.recover())

        self.b3 = self.button()
        self.b3.setButtonText("Toggle Valve")
        self.b3.clicked.connect(lambda: self.valve.toggle())

        self.b4 = self.button()
        self.b4.setButtonText("Toggle Pump")
        self.b4.clicked.connect(lambda: self.pump.toggle())

        self.b5 = self.button()
        self.b5.setButtonText("Home")
        self.b5.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    def SGWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.sensorGraph)
        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)
        self.layout.addWidget(self.b5)

        self.setLayout(self.layout)

def main():
    UI = HomeWindow()
    UI.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
