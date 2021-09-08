import numpy as np
import os
import sys
import time

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


class button(QPushButton):
	def __init__(self, name=None):
		super(button, self).__init__()
		self.setText(name)

	def setButtonColor(self, color):
		self.setStyleSheet('background-color: {}'.format(color))

	def setButtonText(self, text):
		self.setText(text)


class csSpinBox(QDoubleSpinBox):
	def __init__(self, value=0, max=1000, min=0, step=10, suffix="ppm"):
		super(csSpinBox, self).__init__()
		self.setValue(value)
		self.setRange(min, max)
		self.setSingleStep(step)
		self.setSuffix(suffix)


class graph(pg.PlotWidget):
	def __init__(self):
		super(graph, self).__init__()
		self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")


class sensor(QThread):
	mainSignal = pyqtSignal(float)

	def __init__(self, shift=None, adc=None, channel=None):
		super(sensor, self).__init__()
		self.shift = shift

		self.adc = adc
		self.channel = channel
		self.GAIN = 2 / 3

		self.signalVal = 0
		self.timer = QTimer()
		self.timer.timeout.connect(lambda: self.update())
		self.counter = 0
		self.timer.start(10)

	def update(self):
		self.signalVal = self.sVal2PPM()
		self.mainSignal.emit(self.signalVal)

	def sVal2PPM(self):
		return float((self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144) #  * 100

	def startSensor(self):
		if not self.timer.isActive():
			self.timer.start(100)

	def stopSensor(self):
		if self.timer.isActive():
			self.timer.stop()

	def getAvg(self, val):
		self.val = 0
		for i in range(val):
			self.val += self.sVal2PPM()

		return self.val/val


class Stepper(QThread):
    def __init__(self, channel):
        super(Stepper, self).__init__()
        self.motor = channel
        self.currentPos = 0
        self.stepDirection = stepper.FORWARD
        self.stepStyle = stepper.SINGLE
        self.motor.release()
        # self.stepperMinVal = -20
        # self.stepperMaxVal = 140
        self.stepperPos = "Recover"

    def expose(self):
        if not self.stepperPos == "exposed":
            self.stepDirection = stepper.FORWARD
            print("Exposing")
            self.step(370)
            self.stepperPos = "exposed"
        self.motor.release()

    def recover(self):
        if not self.stepperPos == "recovered":
            self.stepDirection = stepper.BACKWARD
            self.step(370)
            print("Recovering")
            self.stepperPos = "recovered"
        self.motor.release()

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


class MOTOR(QThread):
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

	def run4Time(self, runtime): # TIME IN SECONDS
		self.motor.throttle = self.throttleVal
		QTimer.singleShot(runtime*1000, lambda: self.deactivate())


class baseWindow(QWidget):
	def __init__(self):
		super(baseWindow, self).__init__()
		self.loadWindowSettings()

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
		self.pump = MOTOR(self.kit.motor4, "Pump", 1)

		self.valve.deactivate()
		self.pump.deactivate()
		self.SM.motor.release()
		print("Components Loaded and turned Off")

		self.sensor1 = sensor(adc=self.adc, channel=0)
		self.sensor2 = sensor(adc=self.adc, channel=2)
		self.sensor3 = sensor(adc=self.adc, channel=3)
		self.sensor1.mainSignal.connect(self.updateSensor1)
		self.sensor2.mainSignal.connect(self.updateSensor2)
		self.sensor3.mainSignal.connect(self.updateSensor3)
		self.sensor1.start()
		self.sensor2.start()
		self.sensor3.start()

	def loadData(self):
		self.graph = graph()

		self.timeArray = list(range(200))
		self.sensor1Array = [0 for _ in range(200)]
		self.sensor2Array = [0 for _ in range(200)]
		self.sensor3Array = [0 for _ in range(200)]

		self.mcc = pg.mkPen(color=(47, 209, 214), width=2)
		self.blc = pg.mkPen(color=(127, 83, 181), width=2, style=QtCore.Qt.DotLine)
		self.sensor1Plot = self.graph.plot(self.timeArray, self.sensor1Array, pen=self.mcc)
		self.sensor2Plot = self.graph.plot(self.timeArray, self.sensor2Array, pen='r')
		self.sensor3Plot = self.graph.plot(self.timeArray, self.sensor3Array, pen=self.blc)

		self.graph.setYRange(0, 5)

		self.sensor1Label = QLabel()
		self.sensor2Label = QLabel()
		self.sensor3Label = QLabel()

	@pyqtSlot(float)
	def updateSensor1(self, arr):
		self.sensor1Array = self.sensor1Array[1:]
		self.sensor1Array.append(arr)
		self.sensor1Plot.setData(self.timeArray, self.sensor1Array)
		self.sensor1Label.setText("Microchannel Sensor: {:.3f}".format(np.mean(self.sensor1Array[100:])))

	@pyqtSlot(float)
	def updateSensor2(self, arr):
		self.sensor2Array = self.sensor2Array[1:]
		self.sensor2Array.append(arr)
		self.sensor2Plot.setData(self.timeArray, self.sensor2Array)
		self.sensor2Label.setText("Chamber Sensor: {:.3f}".format(np.mean(self.sensor2Array[100:])))

	@pyqtSlot(float)
	def updateSensor3(self, arr):
		self.sensor3Array = self.sensor3Array[1:]
		self.sensor3Array.append(arr)
		self.sensor3Plot.setData(self.timeArray, self.sensor3Array)
		self.sensor3Label.setText("Baseline Sensor: {:.3f}".format(np.mean(self.sensor3Array[100:])))

	def loadNewWindow(self, win):
		if win == 0:
			self.nw = purgeWindow
		elif win == 1:
			self.nw = testWindow
		elif win == 2:
			self.nw = graphWindow
		elif win == 3:
			self.nw = settingsWindow
		else:
			self.nw = homeWindow
		self.nw.show()
		self.close()


class homeWindow(baseWindow, QWidget):
	def __init__(self):
		super(homeWindow, self).__init__()
		self.loadData()
		self.loadComponents()
		self.HWButtonSetup()
		self.loadUI()

	def HWButtonSetup(self):
		self.b1 = button("Purge")
		self.b1.clicked.connect(lambda: self.loadNewWindow(0))

		self.b2 = button("Start Test")
		self.b2.clicked.connect(lambda: self.loadNewWindow(1))

		self.b3 = button("Graph")
		self.b3.clicked.connect(lambda: self.loadNewWindow(2))

		self.b4 = button()
		self.b4.setButtonText("Settings")
		self.b4.clicked.connect(lambda: self.loadNewWindow(3))

		self.b5 = button("Exit")
		self.b5.clicked.connect(lambda: self.exitFunction())

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

	def loadUI(self):
		self.layout = QGridLayout()

		self.layout.addWidget(self.b1)
		self.layout.addWidget(self.b2)
		self.layout.addWidget(self.b3)
		self.layout.addWidget(self.b4)
		self.layout.addWidget(self.b5)

		self.setLayout(self.layout)


class purgeWindow(baseWindow, QWidget):
	def __init__(self):
		super(purgeWindow, self).__init__()
		self.loadData()
		self.loadComponents()
		self.buttonSetup()
		self.timerSetup()
		self.loadUI()

	def buttonSetup(self):
		self.b1 = button("Purge")
		self.b1.clicked.connect(lambda: self.purge())

		self.b2 = button("Stop")
		self.b2.clicked.connect(lambda: self.stop())

		self.b3 = button("Start Test")
		self.b3.clicked.connect(lambda: self.loadNewWindow(1))

		self.b4 = button("Home")
		self.b4.clicked.connect(lambda: self.loadNewWindow(6))

	def timerSetup(self):
		self.purgeTimer = QTimer()
		self.purgeTimer2 = QTimer()
		self.purgeTimer.setSingleShot(True)
		self.purgeTimer2.setSingleShot(True)
		self.purgeTimer.timeout.connect(lambda: self.SM.expose())
		self.purgeTimer2.timeout.connect(lambda: self.stop())
		self.purge1Time = 30000  # normally 20000
		self.purge2Time = 45000  # normally 30000

	def purge(self):
		self.valve.activate()
		self.pump.activate()

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

	def loadUI(self):
		self.layout = QGridLayout()
		self.layout.addWidget(self.graph)
		self.layout.addWidget(self.b1)
		self.layout.addWidget(self.b2)
		self.layout.addWidget(self.b3)
		self.layout.addWidget(self.b4)
		self.setLayout(self.layout)


if __name__ == "__main__":
	UI = homeWindow().show()
	sys.exit(app.exec_())

