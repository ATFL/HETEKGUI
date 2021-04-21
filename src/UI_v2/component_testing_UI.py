
import sys
import board

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg

import Adafruit_ADS1x15 as adc
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

app = QApplication(sys.argv)


class GUI(QWidget):
	# class MOS:
	# 	def __init__(self, adc, channel):
	# 		super(GUI.MOS, self).__init__()
	# 		self.GAIN = 2 / 3
	# 		self.adc = adc
	# 		self.channel = channel
	#
	# 	def read(self):
	# 		self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
	# 		return self.conversion_value

	class graph(pg.PlotWidget):
		def __init__(self):
			super(GUI.graph, self).__init__()
			self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

	class Stepper:
		def __init__(self, channel):
			super(GUI.Stepper, self).__init__()
			self.motor = channel
			self.currentPos = 0
			self.stepDirection = stepper.FORWARD
			self.stepStyle = stepper.SINGLE
			self.motor.release()

		def expose(self):
			self.stepDirection = stepper.FORWARD
			self.step(110)

		def recover(self):
			self.stepDirection = stepper.BACKWARD
			self.step(110)

		def step(self, steps):
			for i in range(steps):
				if -20 < self.currentPos < 130:
					QTimer.singleShot(0.01, lambda: self.motor.oneStep(direction=self.stepDirection, style=self.stepStyle))
					if self.stepDirection == stepper.FORWARD:
						self.currentPos = self.currentPos - 1
					else:
						self.currentPos = self.currentPos + 1
				else:
					print("Out of Bounds")

		def moveLeft(self):
			self.stepDirection = stepper.FORWARD
			self.step(2)

		def moveRight(self):
			self.stepDirection = stepper.BACKWARD
			self.step(2)

	class MOTOR:
		def __init__(self, channel):
			super(GUI.MOTOR, self).__init__()
			self.motor = channel
			self.status = False

		def activate(self):
			if not self.status:
				self.motor.throttle = 1
				self.status = True

		def deactivate(self):
			if self.status:
				self.motor.throttle = 0
				self.status = False

		def toggle(self):
			if self.status:
				self.deactivate()
			else:
				self.activate()

	class button(QPushButton):
		def __init__(self, *args, **kwargs):
			super(GUI.button, self).__init__()
			self.setText("Button Name")

		def setButtonColor(self, color):
			self.setStyleSheet('background-color: {}'.format(color))

		def setButtonText(self, text):
			self.setText(text)

		def setButtonAction(self, action):
			self.clicked.connect(lambda: action)

	def __init__(self):
		super(GUI, self).__init__()
		self.systemSetup()
		self.buttonSetup()
		self.UI()

	def systemSetup(self):
		self.kit = MotorKit(i2c=board.I2C())
		self.adc = adc.ADS1115(0x48)
		self.SM = self.Stepper(self.kit.stepper1)
		self.valve = self.MOTOR(self.kit.motor3)
		self.pump = self.MOTOR(self.kit.motor4)

		# self.sensor1 = self.MOS(self.adc, 0)
		# self.sensor2 = self.MOS(self.adc, 1)
		# self.sensor3 = self.MOS(self.adc, 2)

	def buttonSetup(self):
		self.b1 = self.button()
		self.b1.setButtonText("Expose")
		self.b1.setButtonAction(self.SM.expose())

		self.b2 = self.button()
		self.b2.setButtonText("Recover")
		self.b2.setButtonAction(self.SM.recover())

		self.b3 = self.button()
		self.b3.setButtonText("<<")
		self.b3.setButtonAction(self.SM.moveLeft())

		self.b4 = self.button()
		self.b4.setButtonText(">>")
		self.b4.setButtonAction(self.SM.moveRight())

		self.b5 = self.button()
		self.b5.setButtonText("Toggle Valve")
		self.b5.setButtonAction(self.valve.toggle())

		self.b6 = self.button()
		self.b6.setButtonText("Toggle Pump")
		self.b6.setButtonAction(self.pump.toggle())

	# def graphSetup(self):
	# 	self.sensorGraph = self.graph()
	# 	self.sensorGraph.setYRange(0, 5)
	#
	# 	self.timeArray = list(range(200))
	# 	self.sensor1Array = [0 for _ in range(200)]
	# 	self.sensor2Array = [0 for _ in range(200)]
	# 	self.sensor3Array = [0 for _ in range(200)]
	#
	# 	self.sensor1Plot = self.sensorGraph.plot(self.timeArray, self.sensor1Array, pen='r')
	# 	self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor2Array, pen='g')
	# 	self.sensor2Plot = self.sensorGraph.plot(self.timeArray, self.sensor3Array, pen='b')
	#
	# 	def updateGraph():
	# 		self.sensor1Array = self.sensor1Array[1:]
	# 		self.sensor2Array = self.sensor2Array[1:]
	# 		self.sensor3Array = self.sensor3Array[1:]
	# 		self.sensor1Array.append(self.sensor1.read())
	# 		self.sensor2Array.append(self.sensor2.read())
	# 		self.sensor3Array.append(self.sensor3.read())
	#
	# 		self.sensor1Plot.setData(self.timeArray, self.sensor1Array)
	# 		self.sensor2Plot.setData(self.timeArray, self.sensor2Array)
	# 		self.sensor3Plot.setData(self.timeArray, self.sensor3Array)
	#
	# 	self.graphTimer = QTimer()
	# 	self.graphTimer.timeout.connect(lambda: updateGraph())
	# 	self.graphTimer.start(100)

	def UI(self):
		self.layout = QGridLayout()

		# self.layout.addWidget(self.sensorGraph, 0, 0, 5, 5)
		self.layout.addWidget(self.b1, 6, 0, 1, 1)
		self.layout.addWidget(self.b2, 6, 1, 1, 1)
		self.layout.addWidget(self.b3, 7, 0, 1, 1)
		self.layout.addWidget(self.b4, 7, 1, 1, 1)
		self.layout.addWidget(self.b5, 6, 2, 1, 1)
		self.layout.addWidget(self.b6, 7, 2, 1, 1)

		self.setLayout(self.layout)


def main():
	UI = GUI()
	UI.show()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()