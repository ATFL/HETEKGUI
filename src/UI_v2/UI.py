import numpy as np
import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from datetime import datetime

import yaml


app = QApplication(sys.argv)


class GUI(QWidget):
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

	class graph(pg.PlotWidget):
		def __init__(self):
			super(GUI.graph, self).__init__()
			self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

	class MotorHat:
		def __init__(self):
			super(GUI.MotorHat, self).__init__()
			pass

	class Stepper(MotorHat):
		def __init__(self, channel):
			super(GUI.Stepper, self).__init__()
			self.channel = channel
			pass

	class Motor(MotorHat):
		def __init__(self, channel, name):
			super(GUI.Motor, self).__init__()
			pass

	class MOS:
		def __init__(self, adc, channel):
			super(GUI.MOS, self).__init__()
			self.GAIN = 2 / 3
			self.adc = adc
			self.channel = channel

		def read(self):
			self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
			return self.conversion_value

	class PurgeWindow(QWidget):
		def __init__(self):
			super(GUI.PurgeWindow, self).__init__()
			self.UI()

			

	def __init__(self, *args, **kwargs):
		super(GUI, self).__init__()
		self.loadSettings()
		self.setStyleSheet('background-color: {}'.format(self.bg_color))
		self.setGeometry(0, 0, self.width, self.height)

	def loadSettings(self):
		self.width = 480
		self.height = 320
		self.bg_color = '#484848'

	def


def main():
	UI = GUI()
	UI.show()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()
