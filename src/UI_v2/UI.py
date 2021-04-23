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

import yaml

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
			print("Exposing")
			self.step(110)

		def recover(self):
			self.stepDirection = stepper.BACKWARD
			print("Recovering")
			self.step(110)

		def step(self, steps):
			for i in range(steps):
				QTimer.singleShot(10, lambda: self.motor.onestep(direction=self.stepDirection, style=self.stepStyle))
				if self.stepDirection == stepper.FORWARD:
					self.currentPos = self.currentPos - 1
				else:
					self.currentPos = self.currentPos + 1
			self.motor.release()

		def moveLeft(self):
			self.stepDirection = stepper.FORWARD
			self.step(2)

		def moveRight(self):
			self.stepDirection = stepper.BACKWARD
			self.step(2)

	class MOTOR:
		def __init__(self, channel, name):
			super(GUI.MOTOR, self).__init__()
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

	class button(QPushButton):
		def __init__(self, *args, **kwargs):
			super(GUI.button, self).__init__()
			self.setText("Button Name")

		def setButtonColor(self, color):
			self.setStyleSheet('background-color: {}'.format(color))

		def setButtonText(self, text):
			self.setText(text)

		# def setButtonAction(self, action):
		# 	self.clicked.connect(lambda: action)

	class HomeWindow(QWidget):
		def __init__(self):
			super(GUI.HomeWindow, self).__init__()
			self.HWUI()

		def HWButtonSetup(self):
			self.b1 = self.button()
			self.b1.setButtonText("Start New Test")
			self.b1.clicked.connect(lambda: self.showSTW())

		def showPW(self):
			self.PW = GUI.PurgeWindow()
			self.PW.show()
			self.close()

		def showSW(self):
			self.SW = GUI.SettingsWindow()
			self.SW.show()
			self.close()

		def showSTW(self):
			self.STW = GUI.StartTestWindow()
			self.STW.show()
			self.close()


		def HWUI(self):


	class PurgeWindow(QWidget):
		def __init__(self):
			super(GUI.PurgeWindow, self).__init__()
			self.PWButtonSetup()
			self.PWUI()

		def PWButtonSetup(self):
			self.b1 = B
			

	def __init__(self, *args, **kwargs):
		super(GUI, self).__init__()
		self.loadSettings()
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)

	def loadSettings(self):
		self.width = 480
		self.height = 320
		self.bg_color = '#484848'

	def loadComponents(self):
		self.kit = MotorKit(i2c=board.I2C())
		# self.adc = adc.ADS1115(0x48)
		self.SM = self.Stepper(self.kit.stepper1)
		self.valve = self.MOTOR(self.kit.motor3, "Valve")
		self.pump = self.MOTOR(self.kit.motor4, "Pump")

		self.valve.deactivate()
		self.pump.deactivate()

		# self.sensor1 = self.MOS(self.adc, 0)
		# self.sensor2 = self.MOS(self.adc, 1)
		# self.sensor3 = self.MOS(self.adc, 2)


def main():
	UI = GUI()
	UI.show()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()
