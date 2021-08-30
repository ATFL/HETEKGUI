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


class Stepper(QThread):
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
            self.stepDirection = stepper.FORWARD
            print("Exposing")
            self.step(370)
            self.stepperPos = "exposed"

    def recover(self):
        if not self.stepperPos == "recovered":
            self.stepDirection = stepper.BACKWARD
            self.step(370)
            print("Recovering")
            self.stepperPos = "recovered"

    def moveLeft(self):
        self.stepDirection = stepper.FORWARD
        self.step(10)
        print("<<")
        self.stepperPos = "mid"

    def moveRight(self):
        self.stepDirection = stepper.BACKWARD
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
        if self.stepDirection == stepper.FORWARD:
            self.currentPos = self.currentPos + 1
        else:
            self.currentPos = self.currentPos - 1


class MOTOR:
    def __init__(self, channel, name, throttleVal):
        super(MOTOR, self).__init__()
        self.motor = channel
        self.name = name
        self.throttleVal = throttleVal

        self.status = False

    def activate(self):
        try:
            self.motor.throttle = self.throttleVal
            self.status = True
            print("{}: ON".format(self.name))

        except:
            print("Weird power shit")

    def deactivate(self):
        try:
            self.motor.throttle = 0
            self.status = False
            print("{}: OFF".format(self.name))
        except:
            print("Weird Power Shit")

    def toggle(self):
        if self.status:
            self.deactivate()
        else:
            self.activate()


class button(QPushButton):
    def __init__(self):
        super(button, self).__init__()

    def setButtonColor(self, color):
        self.setStyleSheet('background-color: {}'.format(color))

    def setButtonText(self, text):
        self.setText(text)


class HomeWindow(QWidget):
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
        self.kit = MotorKit(0x63)
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def HWButtonSetup(self):
        self.b1 = button()
        self.b1.setButtonText("Start Test")
        self.b1.clicked.connect(lambda: self.showSTW())

        self.b2 = button()
        self.b2.setButtonText("Purge")
        self.b2.clicked.connect(lambda: self.showPW())

        self.b3 = button()
        self.b3.setButtonText("Control Panel")
        self.b3.clicked.connect(lambda: self.showCPW())

        self.b4 = button()
        self.b4.setButtonText("Sensor Graph")
        self.b4.clicked.connect(lambda: self.showSGW())

        self.b5 = button()
        self.b5.setButtonText("Settings")
        self.b5.clicked.connect(lambda: self.showSW())

        self.b6 = button()
        self.b6.setButtonText("Exit")
        self.b6.clicked.connect(lambda: self.exitFunction())

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

    def exitFunction(self):
        self.exitMsg = QMessageBox()
        self.exitMsg.setText("Do you Want to shutdown?")
        self.exitMsg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.em = self.exitMsg.exec()
        if self.em == QMessageBox.Yes:
            QApplication.closeAllWindows()
            os.system("sudo shutdown now")
        else:
            QApplication.closeAllWindows()

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
    def __init__(self):
        super(PurgeWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.PWButtonSetup()
        self.purgeTimer = QTimer()
        self.purgeTimer2 = QTimer()
        self.purgeTimer.setSingleShot(True)
        self.purgeTimer2.setSingleShot(True)
        self.purgeTimer.timeout.connect(lambda: self.SM.expose())
        self.purgeTimer2.timeout.connect(lambda: self.stop())
        self.purge1Time = 20000  # normally 20000
        self.purge2Time = 30000  # normally 30000
        self.PWUI()

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
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def PWButtonSetup(self):
        self.b1 = button()
        self.b1.setButtonText("Purge")
        self.b1.clicked.connect(lambda: self.purge())

        self.b2 = button()
        self.b2.setButtonText("Home")
        self.b2.clicked.connect(lambda: self.showHW())

        self.b3 = button()
        self.b3.setButtonText("Control Panel")
        self.b3.clicked.connect(lambda: self.showCPW())

        self.b4 = button()
        self.b4.setButtonText("Stop")
        self.b4.clicked.connect(lambda: self.stop())

        self.b5 = button()
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
        self.pump.activate()
        self.valve.activate()

        self.purgeTimer.start(self.purge1Time)
        self.purgeTimer2.start(self.purge2Time)

    def stop(self):
        if self.purgeTimer.isActive():
            self.purgeTimer.stop()
        if self.purgeTimer2.isActive():
            self.purgeTimer.stop()
        self.pump.deactivate()
        self.valve.deactivate()
        self.SM.recover()

    def PWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)
        self.layout.addWidget(self.b4)
        self.layout.addWidget(self.b5)

        self.setLayout(self.layout)


class SettingsWindow(QWidget):

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
        self.kit = MotorKit(0x63)
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()
        print("Components Loaded")

    def SWButtonSetup(self):
        self.b1 = button()
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
    def __init__(self):
        super(StartTestWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.STWButtonSetup()
        self.graphSetup()

        self.path = os.getcwd()
        self.dataPath = "{}/data/".format(self.path)

        self.sampleCollectTime = 20000  # normally 20000
        self.exposeTime = 10000  # normally 10000
        self.recoverTime = 50000  # normally 50000
        self.endTestTime = 120000  # normally 120000

        self.testTimer = QTimer()
        self.dataTimer = QTimer()
        self.exposeTimer = QTimer()
        self.recoveryTimer = QTimer()
        self.endTimer = QTimer()
        self.dataTimer.timeout.connect(lambda: self.updateData())
        self.exposeTimer.setSingleShot(True)
        self.recoveryTimer.setSingleShot(True)
        self.endTimer.setSingleShot(True)

        self.STWUI()

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
        self.SM.start()
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)
        # POOP
        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()

        self.sensor1 = MOS(self.adc, 0)
        self.sensor2 = MOS(self.adc, 3)
        self.sensor3 = MOS(self.adc, 2)

        self.sensorGraph = graph()

        print("Components Loaded")

    def graphSetup(self):
        self.sensorGraph.clear()
        print("graph cleared and reset")
        self.timeArray = [0]
        self.sensor1Array = [self.sensor1.read()]
        self.sensor2Array = [self.sensor2.read()]
        self.sensor3Array = [self.sensor3.read()]

        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen='r')
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='g')
        self.sensor3Plot = self.sensorGraph.plot(self.timeArray, self.sensor3Array, pen='b')

    def STWButtonSetup(self):
        self.b1 = button()
        self.b1.setButtonText("Start")
        self.b1.clicked.connect(lambda: self.initializeTest())

        self.b2 = button()
        self.b2.setButtonText("Stop")
        self.b2.clicked.connect(lambda: self.stop())
        self.b2.setDisabled(True)

        self.b3 = button()
        self.b3.setButtonText("Home")
        self.b3.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.HW = HomeWindow()
        self.HW.show()
        self.close()

    # def initializeTest(self):
    #     # Collect Sample
    #     self.SM.recover()
    #     self.pump.activate()
    #     self.valve.activate()
    #     self.testTimer.setSingleShot(True)
    #     self.testTimer.timeout.connect(lambda: self.data_collect())
    #     self.testTimer.start(self.sampleCollectTime)
    #     self.dataTimer.start(100)
    #     self.b1.setDisabled(True)
    #     self.b2.setDisabled(False)
    #     self.b3.setDisabled(True)
    #     print("Initialize Text")

    def initializeTest(self):
        # Collect Sample
        try:
            self.SM.recover()
            print("Stepper motor home")
        except:
            print("SM recover failed")
        try:
            #self.pump.activate()
            print("pump activated")

        except:
            print("pump activation failed")
        try:
            self.valve.activate()
            print("valve activated")

        except:
            print("valve activation failed")
        print("starting timer")
        self.testTimer.setSingleShot(True)
        self.testTimer.timeout.connect(lambda: self.data_collect())
        self.testTimer.start(self.sampleCollectTime)
        self.dataTimer.start(100)
        self.b1.setDisabled(True)
        self.b2.setDisabled(False)
        self.b3.setDisabled(True)
        print("Initialize Text")

    def data_collect(self):
        print("Running Test, new data collecting")
        self.pump.deactivate()
        self.valve.deactivate()
        self.dataTimer.stop()
        self.graphSetup()

        self.dataTimer.start(100)

        self.exposeTimer.timeout.connect(lambda: self.SM.expose())
        self.exposeTimer.start(self.exposeTime)

        self.recoveryTimer.timeout.connect(lambda: self.SM.recover())
        self.recoveryTimer.start(self.recoverTime)

        self.endTimer.timeout.connect(lambda: self.stop())
        self.endTimer.start(self.endTestTime)

    def updateData(self):
        self.timeArray.append(self.timeArray[-1] + 0.1)
        self.sensor1Array.append(self.sensor1.read())
        self.sensor2Array.append(self.sensor2.read())
        self.sensor3Array.append(self.sensor3.read())

        self.sensor1Plot.setData(self.timeArray, self.sensor1Array)
        self.sensor2Plot.setData(self.timeArray, self.sensor2Array)
        self.sensor3Plot.setData(self.timeArray, self.sensor3Array)

    def stop(self):
        self.pump.deactivate()
        self.valve.deactivate()
        self.SM.recover()
        if self.testTimer.isActive():
            self.testTimer.stop()
        if self.dataTimer.isActive():
            self.dataTimer.stop()
        if self.exposeTimer.isActive():
            self.exposeTimer.stop()
        if self.recoveryTimer.isActive():
            self.recoveryTimer.stop()
        if self.endTimer.isActive():
            self.endTimer.stop()

        self.filename = "d3v3_{}.csv".format(datetime.now().strftime('%m%d%H%M%S'))
        self.save = self.askSave()
        if self.save == QMessageBox.Ok:
            self.saveData()
        self.b3.setDisabled(False)

    def askSave(self):
        self.saveMsg = QMessageBox()
        self.saveMsg.setIcon(QMessageBox.Information)
        self.saveMsg.setText("Do you want to save the data?")
        self.saveMsg.setInformativeText("File will be saved as: {}".format(self.filename))
        self.saveMsg.setWindowTitle("Save Data")
        self.saveMsg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return self.saveMsg.exec()

    def saveData(self):
        self.filenameTotal = self.dataPath + self.filename
        self.stackedArray = [self.timeArray, self.sensor1Array, self.sensor2Array, self.sensor3Array]
        np.savetxt(self.filenameTotal, self.stackedArray, fmt='%.10f', delimiter=',')
        self.saveMessageEnd = QMessageBox()
        self.saveMessageEnd.setIcon(QMessageBox.Information)
        self.saveMessageEnd.setText("Saved")
        self.saveMessageEnd.setInformativeText("File Saved as: {}".format(self.filename))
        self.saveMessageEnd.setStandardButtons(QMessageBox.Ok)

    def STWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.sensorGraph)

        self.layout.addWidget(self.b1)
        self.layout.addWidget(self.b2)
        self.layout.addWidget(self.b3)

        self.setLayout(self.layout)


class ControlPanelWindow(QWidget):
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
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()

        print("Components Loaded")

    def CPWButtonSetup(self):
        self.b1 = button()
        self.b1.setButtonText("Expose")
        self.b1.clicked.connect(lambda: self.SM.expose())

        self.b2 = button()
        self.b2.setButtonText("Recover")
        self.b2.clicked.connect(lambda: self.SM.recover())

        self.buttonStatus = False

        self.b3 = button()
        self.b3.setButtonText("<<")
        # self.b3.clicked.connect(lambda: self.SM.moveLeft())
        self.b3.pressed.connect(lambda: self.move(0))
        self.b3.released.connect(lambda: self.endMove())

        self.b4 = button()
        self.b4.setButtonText(">>")
        # self.b4.clicked.connect(lambda: self.SM.moveRight())
        self.b4.pressed.connect(lambda: self.move(1))
        self.b4.released.connect(lambda: self.endMove())

        self.b5 = button()
        self.b5.setButtonText("Toggle Valve")
        self.b5.clicked.connect(lambda: self.valve.toggle())

        self.b6 = button()
        self.b6.setButtonText("Toggle Pump")
        self.b6.clicked.connect(lambda: self.pump.toggle())

        self.b7 = button()
        self.b7.setButtonText("Zero Stepper Motor")
        self.b7.clicked.connect(lambda: self.SM.zero())

        self.b8 = button()
        self.b8.setButtonText("Home")
        self.b8.clicked.connect(lambda: self.showHW())

    def move(self, direction):
        if direction == 0:
            self.SM.stepDirection = stepper.BACKWARD
        else:
            self.SM.stepDirection = stepper.FORWARD
        # print("starting movement")
        self.buttonStatus = True
        while self.buttonStatus:
            app.processEvents()
            self.SM.move()
        self.SM.motor.release()

    def endMove(self):
        self.buttonStatus = False
        self.SM.motor.release()
        print("Current Position: {}".format(self.SM.currentPos))

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
    def __init__(self):
        super(SensorGraphWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.SGWButtonSetup()

        self.graphTimer = QTimer()
        self.graphTimer.timeout.connect(lambda: self.liveGraph())

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
        self.kit = MotorKit(0x63)
        self.adc = adc.ADS1115(0x48)
        self.SM = Stepper(self.kit.stepper1)
        self.valve = MOTOR(self.kit.motor3, "Valve", 1)
        self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)

        self.valve.deactivate()
        self.pump.deactivate()
        self.SM.motor.release()

        self.sensor1 = MOS(self.adc, 0)
        self.sensor2 = MOS(self.adc, 3)
        self.sensor3 = MOS(self.adc, 2)

        print("Components Loaded")

    def graphSetup(self):
        self.sensorGraph = graph()

        self.timeArray = list(range(200))
        self.sensor1Array = [0 for _ in range(200)]
        self.sensor2Array = [0 for _ in range(200)]
        self.sensor3Array = [0 for _ in range(200)]

        self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen='r')
        self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='g')
        self.sensor3Plot = self.sensorGraph.plot(self.timeArray, self.sensor3Array, pen='b')
        self.graphTimer.start(100)

    def liveGraph(self):
        self.sensor1Array = self.sensor1Array[1:]
        self.sensor2Array = self.sensor2Array[1:]
        self.sensor3Array = self.sensor3Array[1:]

        self.sensor1Array.append(self.sensor1.read())
        self.sensor2Array.append(self.sensor2.read())
        self.sensor3Array.append(self.sensor3.read())

        self.sensor1Plot.setData(self.timeArray, self.sensor1Array)
        self.sensor2Plot.setData(self.timeArray, self.sensor2Array)
        self.sensor3Plot.setData(self.timeArray, self.sensor3Array)

    def SGWButtonSetup(self):
        self.b1 = button()
        self.b1.setButtonText("Expose")
        self.b1.clicked.connect(lambda: self.SM.expose())

        self.b2 = button()
        self.b2.setButtonText("Recover")
        self.b2.clicked.connect(lambda: self.SM.recover())

        self.b3 = button()
        self.b3.setButtonText("Toggle Valve")
        self.b3.clicked.connect(lambda: self.valve.toggle())

        self.b4 = button()
        self.b4.setButtonText("Toggle Pump")
        self.b4.clicked.connect(lambda: self.pump.toggle())

        self.b5 = button()
        self.b5.setButtonText("Home")
        self.b5.clicked.connect(lambda: self.showHW())

    def showHW(self):
        self.graphTimer.stop()
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
