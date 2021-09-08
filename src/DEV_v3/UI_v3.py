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
		print(type(self.signalVal))
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
		self.stepStyle = stepper.DOUBLE
		self.motor.release()
		# self.stepperPos = "Recover"

	def expose(self):
		self.stepDirection = stepper.FORWARD
		print("Exposing")
		self.step(370)
		self.motor.release()

	def recover(self):
		self.stepDirection = stepper.BACKWARD
		self.step(370)
		print("Recovering")
		self.motor.release()

	def moveLeft(self):
		self.stepDirection = stepper.FORWARD
		self.step(10)
		print("<<")

	def moveRight(self):
		self.stepDirection = stepper.BACKWARD
		self.step(10)
		print(">>")

	def zero(self):
		self.currentPos = 0

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


if __name__ == "__main__":
	UI = baseWindow()
	UI.loadData()
	UI.loadComponents()
	UI.show()
	sys.exit(app.exec_())

