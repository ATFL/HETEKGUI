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


class GUI(QWidget):
	class MOS:
		def __init__(self, adc, channel):
			super(GUI.MOS, self).__init__()
			self.GAIN = 2 / 3
			self.adc = adc
			self.channel = channel

		def read(self):
			self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
			return self.conversion_value

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
				if GUI.stepperMinVal < self.stepDirection < GUI.stepperMaxVal:
					QTimer.singleShot(10, lambda: self.motor.onestep(direction=self.stepDirection, style=self.stepStyle))
					if self.stepDirection == stepper.FORWARD:
						self.currentPos = self.currentPos + 1
					else:
						self.currentPos = self.currentPos - 1
			self.motor.release()

		def moveLeft(self):
			self.stepDirection = stepper.FORWARD
			self.step(2)

		def moveRight(self):
			self.stepDirection = stepper.BACKWARD
			self.step(2)

		def zero(self):
			self.currentPos = 0

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


	class HomeWindow(QWidget):
		def __init__(self):
			super(GUI.HomeWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))

			self.GUI = GUI()
			self.HWButtonSetup()
			self.HWUI()

		def HWButtonSetup(self):
			self.b1 = self.GUI.button()
			self.b1.setButtonText("Start Test")
			self.b1.clicked.connect(lambda: self.showSTW())

			self.b2 = self.GUI.button()
			self.b2.setButtonText("Purge")
			self.b2.clicked.connect(lambda: self.showPW())

			self.b3 = self.GUI.button()
			self.b3.setButtonText("Control Panel")
			self.b3.clicked.connect(lambda: self.showCPW())

			self.b4 = self.GUI.button()
			self.b4.setButtonText("Sensor Graph")
			self.b4.clicked.connect(lambda: self.showSGW())

			self.b5 = self.GUI.button()
			self.b5.setButtonText("Settings")
			self.b5.clicked.connect(lambda: self.showSW())

			self.b6 = self.GUI.button()
			self.b6.setButtonText("Exit")
			self.b6.clicked.connect(lambda: QApplication.closeAllWindows())

		def showPW(self):
			self.PW = self.GUI.PurgeWindow()
			self.PW.show()
			self.close()

		def showSW(self):
			self.SW = self.GUI.SettingsWindow()
			self.SW.show()
			self.close()

		def showSTW(self):
			self.STW = self.GUI.StartTestWindow()
			self.STW.show()
			self.close()

		def showCPW(self):
			self.CPW = self.GUI.ControlPanelWindow()
			self.CPW.show()
			self.close()

		def showSGW(self):
			self.SGW = self.GUI.SensorGraphWindow()
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
		def __init__(self):
			super(GUI.PurgeWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))
			self.GUI = GUI()
			self.PWButtonSetup()
			self.PWUI()

		def PWButtonSetup(self):
			self.b1 = self.GUI.button()
			self.b1.setButtonText("Purge")
			self.b1.clicked.connect(lambda: GUI.purge())

			self.b2 = self.GUI.button()
			self.b2.setButtonText("Home")
			self.b2.clicked.connect(lambda: self.showHW())

			self.b3 = self.GUI.button()
			self.b3.setButtonText("Settings")
			self.b3.clicked.connect(lambda: self.showSW())

			self.b4 = self.GUI.button()
			self.b4.setButtonText("Stop")
			self.b4.clicked.connect(lambda: GUI.stop())

		def showHW(self):
			self.HW = self.GUI.HomeWindow()
			self.HW.show()
			self.close()

		def showSW(self):
			self.SW = self.GUI.SettingsWindow()
			self.SW.show()
			self.close()

		def PWUI(self):
			self.layout = QGridLayout()

			self.layout.addWidget(self.b1)
			self.layout.addWidget(self.b2)
			self.layout.addWidget(self.b3)
			self.layout.addWidget(self.b4)

			self.setLayout(self.layout)

	class SettingsWindow(QWidget):
		def __init__(self):
			super(GUI.SettingsWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))
			self.SWButtonSetup()
			self.SWUI()

		def SWButtonSetup(self):
			self.b1 = self.GUI.button()
			self.b1.setButtonText("Home")
			self.b1.clicked.connect(lambda: self.showHW())

		def showHW(self):
			self.HW = self.GUI.HomeWindow()
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
			super(GUI.StartTestWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))
			self.GUI = GUI()
			self.STWButtonSetup()
			self.graphSetup()
			self.STWUI()

		def STWButton(self):


		def STWUI(self):
			self.layout = QGridLayout()

			self.layout.addWidget(self.b1)
			self.layout.addWidget(self.b2)
			self.layout.addWidget(self.b3)
			self.layout.addWidget(self.b4)

			self.setLayout(self.layout)

	class ControlPanelWindow(QWidget):
		def __init__(self):
			super(GUI.ControlPanelWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))
			self.CPWButtonSetup()
			self.CPWUI()

		def CPWButtonSetup(self):
			self.b1 = self.button()
			self.b1.setButtonText("Expose")
			self.b1.clicked.connect(lambda: GUI.SM.expose())

			self.b2 = self.button()
			self.b2.setButtonText("Recover")
			self.b2.clicked.connect(lambda: GUI.SM.recover())

			self.b3 = self.button()
			self.b3.setButtonText("<<")
			self.b3.clicked.connect(lambda: GUI.SM.moveLeft())

			self.b4 = self.button()
			self.b4.setButtonText(">>")
			self.b4.clicked.connect(lambda: GUI.SM.moveRight())

			self.b5 = self.button()
			self.b5.setButtonText("Toggle Valve")
			self.b5.clicked.connect(lambda: GUI.valve.toggle())

			self.b6 = self.button()
			self.b6.setButtonText("Toggle Pump")
			self.b6.clicked.connect(lambda: GUI.pump.toggle())

			self.b7 = self.button()
			self.b7.setButtonText("Zero Stepper Motor")
			self.b7.clicked.connect(lambda: GUI.SM.zero())

		def CPWUI(self):
			self.layout = QGridLayout()

			self.layout.addWidget(self.b1)
			self.layout.addWidget(self.b2)
			self.layout.addWidget(self.b3)
			self.layout.addWidget(self.b4)
			self.layout.addWidget(self.b5)
			self.layout.addWidget(self.b6)
			self.layout.addWidget(self.b7)

			self.setLayout(self.layout)

	class SensorGraphWindow(QWidget):
		def __init__(self):
			super(GUI.SensorGraphWindow, self).__init__()
			self.setGeometry(0, 0, GUI.width, GUI.height)
			self.setStyleSheet('background-color: {}'.format(GUI.bg_color))
			self.SGWButtonSetup()
			self.SGWUI()

		def SGWButtonSetup(self):


		def SGWUI(self):
			self.layout = QGridLayout()

			self.layout.addWidget(self.b1)
			self.layout.addWidget(self.b2)
			self.layout.addWidget(self.b3)
			self.layout.addWidget(self.b4)

			self.setLayout(self.layout)

	def __init__(self, *args, **kwargs):
		super(GUI, self).__init__()
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)
		self.loadSettings()
		self.loadComponents()

		self.showHW()

	def showHW(self):
		self.HW = GUI.HomeWindow()
		self.HW.show()
		self.close()

	def loadSettings(self):
		self.width = 480
		self.height = 320
		self.bg_color = '#484848'

		self.stepperMaxVal = 130
		self.stepperMinVal = -20
		self.testExposureTime = 10
		self.testRecoveryTime = 50
		self.testTotalTime = 120

		self.purgePhase1Time = 20
		self.purgePhase2Time = 20

	def loadComponents(self):
		self.kit = MotorKit(i2c=board.I2C())
		self.adc = adc.ADS1115(0x48)
		self.SM = self.Stepper(self.kit.stepper1)
		self.valve = self.MOTOR(self.kit.motor3, "Valve")
		self.pump = self.MOTOR(self.kit.motor4, "Pump")

		self.valve.deactivate()
		self.pump.deactivate()
		self.SM.motor.release()

		self.sensor1 = self.MOS(self.adc, 0)
		self.sensor2 = self.MOS(self.adc, 1)
		self.sensor3 = self.MOS(self.adc, 2)

	class Purge:
		def __init__(self):
			super(GUI.Purge, self).__init__()
			self.phase1Time = GUI.purgePhase1Time
			self.phase2Time = GUI.purgePhase2Time


	def purge(self):
		pass

	def liveGraph(self):
		pass

	def test(self):
		pass

	def collectSample(self):
		pass




def main():
	UI = GUI()
	UI.show()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()
