'''
CHANGES FROM UI:
1. THREADED SENSORS AND COMPONENTS ALLOWING FOR SMOOTHER RUNS
2. LBO CONNECTION TO DETECT LOW BATTERY (PENDING)
3. GRAPHICAL FEATURE ON PURGE WINDOW
4. SETTINGS WINDOW CONTROLS TIMING SETTINGS (PENDING)
5. SAVING BUTTON HAS OPTIONAL KEYBOARD INPUT (PENDING)
6. SPINBOX FOR SAVING GAS CONCENTRATIONS (PENDING)
'''

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
	def __init__(self, name):
		super(button, self).__init__()
		self.setText(name)

	def setButtonColor(self, color):
		self.setStyleSheet('background-color: {}'.format(color))

	def setButtonText(self, text):
		self.setText(text)


class csSpinBox(QSpinBox):
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
	mainSignal = pyqtSignal(np.ndarray)

	def __init__(self, shift=None, adc=None, channel=None):
		super(sensor, self).__init__()
		self.shift = shift

		self.adc = adc
		self.channel = channel
		self.GAIN = 2 / 3

		self.signalArray = [0 for _ in range(200)]
		self.timer = QTimer()
		self.timer.timeout.connect(lambda: self.update())
		#self.loadADCSettings()
		self.counter = 0
		self.timer.start(10)

	def update(self):
		self.signalArray = self.signalArray[1:]
		#try:
		#self.signalArray.append(round(((self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144), 3))
		self.signalArray.append(self.sVal2PPM())
		#self.signalArray.append(self.signalArray[-1])

		self.mainSignal.emit(self.signalArray)

	def sVal2PPM(self):
		return ((self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144) #  * 100

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
		self.stepperMinVal = -20
		self.stepperMaxVal = 140
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

	def move4Time(self, runtime):
		self.expose()
		QTimer.singleShot(runtime*1000, lambda: self.recover())


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


class HomeWindow(QWidget):
	def __init__(self):
		super(HomeWindow, self).__init__()
		self.loadWindowSettings()
		self.loadComponents()
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
		print("Components Loaded and turned Off")

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
		self.loadGraphSettings()
		self.PWButtonSetup()
		self.purgeTimer = QTimer()
		self.purgeTimer2 = QTimer()
		self.purgeTimer.setSingleShot(True)
		self.purgeTimer2.setSingleShot(True)
		self.purgeTimer.timeout.connect(lambda: self.SM.expose())
		self.purgeTimer2.timeout.connect(lambda: self.stop())
		self.purge1Time = 20000 # normally 20000
		self.purge2Time = 30000 # normally 30000
		self.PWUI()

	def loadWindowSettings(self):
		self.width = 480
		self.height = 320
		self.bg_color = '#484848'
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)
		print("Window Settings Loaded")

	def loadComponents(self):
		self.adc = adc.ADS1115(0x48)
		self.sensor1 = sensor(adc=self.adc, channel=0)
		self.sensor2 = sensor(adc=self.adc, channel=2)
		self.sensor3 = sensor(adc=self.adc, channel=3)
		self.sensor1.mainSignal.connect(self.updateSensor1)
		self.sensor2.mainSignal.connect(self.updateSensor2)
		self.sensor3.mainSignal.connect(self.updateSensor3)
		self.sensor1.start()
		self.sensor2.start()
		self.sensor3.start()

		self.kit = MotorKit(0x63)
		self.SM = Stepper(self.kit.stepper1)
		self.SM.start()
		self.valve = MOTOR(self.kit.motor3, "Valve", 1)
		self.valve.start()
		self.pump = MOTOR(self.kit.motor4, "Pump", 0.9)
		self.pump.start()
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

	def loadGraphSettings(self):
		self.graph = graph()

		self.timeArray = list(range(200))
		self.sensor1Array = [0 for _ in range(200)]
		self.sensor2Array = [0 for _ in range(200)]
		self.baselineArray = [0 for _ in range(200)]

		self.chicken = pg.mkPen(color=(47, 209, 214), width=2)
		self.redPanda = pg.mkPen(color=(127, 83, 181), width=2, style=QtCore.Qt.DotLine)
		self.sensor1Plot = self.graph.plot(self.timeArray, self.sensor1Array, pen=self.chicken)
		self.sensor2Plot = self.graph.plot(self.timeArray, self.sensor2Array, pen='r')
		self.baselinePlot = self.graph.plot(self.timeArray, self.baselineArray, pen=self.redPanda)

		self.graph.setYRange(0, 5)

		self.sensor1Label = QLabel()
		self.sensor2Label = QLabel()


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