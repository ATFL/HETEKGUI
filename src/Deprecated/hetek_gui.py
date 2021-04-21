import numpy as np
import os
import sys
import board
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from datetime import datetime
import Adafruit_ADS1x15 as ads
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

app = QApplication(sys.argv)


class mainWindow(QWidget):
	class MOS:
		def __init__(self, adc, channel):
			self.GAIN = 2 / 3
			self.adc = adc
			self.channel = channel
			self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144

		def read(self):
			self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
			return self.conversion_value

	class MOS2:
		def __init__(self):
			pass
		def read(self):
			return 0

	class Graph(pg.PlotWidget):
		def __init__(self, parent=None):
			super(mainWindow.Graph, self).__init__()
			self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

	class startTest(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.startTest, self).__init__()
			self.setText('Start Test')

	class stop(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stop, self).__init__()
			self.setText('Stop')

	class liveReading(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.liveReading, self).__init__()
			self.setText('Live Reading')

	class clear(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.clear, self).__init__()
			self.setText('Clear All')

	class stepper_eb(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stepper_eb, self).__init__()
			self.setText('Open MC Valve')

	class stepper_rb(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stepper_rb, self).__init__()
			self.setText('Close MC Valve')

	class valve_op(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.valve_op, self).__init__()
			self.setText('Open Chamber Valve')

	class valve_cl(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.valve_cl, self).__init__()
			self.setText('Close Chamber Valve')

	class pumpOn(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.pumpOn, self).__init__()
			self.setText('Pump On')

	class pumpOff(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.pumpOff, self).__init__()
			self.setText('Pump Off')

	class setBaselineButton(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.setBaselineButton, self).__init__()
			self.setText('Set Sensor Baseline')

	class stepperRightButton(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stepperRightButton, self).__init__()
			self.setText('Stepper Right')

	class stepperLeftButton(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stepperLeftButton, self).__init__()
			self.setText('Stepper Left')

	class stepperZeroButton(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.stepperZeroButton, self).__init__()
			self.setText('Zero Stepper')

	class purge(QPushButton):
		def __init__(self, parent=None):
			super(mainWindow.purge, self).__init__()
			self.setText('Purge System')

	class Stepper:
		def __init__(self):
			super(mainWindow.Stepper, self).__init__()
			self.stepperPosition = 0
			self.rightBoundary = 25

		def move(self, steps):
			self.stepTimer = QTimer()

			def stepF():
				self.kit.stepper1.onestep(direction=stepper.FORWARD)
				self.stepCounter = self.stepCounter + 1
				if self.stepCounter == abs(steps):
					self.stepTimer.stop()

			def stepB():
				self.kit.stepper1.onestep(direction=stepper.BACKWARD)
				self.stepCounter = self.stepCounter + 1
				if self.stepCounter == abs(steps):
					self.stepTimer.stop()

			if steps > 0:
				self.stepTimer.timeout.connect(stepF())
			elif steps < 0:
				self.stepTimer.timeout.connect(stepB())

			self.stepCounter = 0
			self.stepTimer.start(10)

			self.stepperPosition = self.stepperPosition + steps

		def zero(self):
			self.stepperPosition = 0

		def expose(self):
			self.difference = self.rightBoundary - self.stepperPosition
			self.move(self.difference)

		def recover(self):
			self.difference =-self.rightBoundary
			self.move(self.difference)

	def __init__(self, *args, **kwargs):
		super(mainWindow, self).__init__(*args, **kwargs)
		# TESTING PARAMETERS
		self.startExposeTime = 5
		self.startRecoverTime = 10
		self.endTestTime = 15
		self.dataRate = 10
		# PURGING PARAMETERS
		self.purgeMCTime = 20
		self.purgeTotalTime = 30
		# SAMPLE COLLECTION PARAMETERS
		self.sampleStopTime = 10

		self.curDir = os.getcwd()
		self.saveDir = self.curDir + '/Data/v1.1'

		self.timeVector = []
		self.sensor1Vector = []
		self.sensor2Vector = []

		self.systemSetup()
		self.widgetSetup()
		self.uiSetup()

	def systemSetup(self):
		self.kit = MotorKit(i2c=board.I2C())
		#self.adc = ads.ADS1115(0x48)
		self.sensor1 = self.MOS2()
		self.sensor2 = self.MOS2()
		self.stepperA = self.Stepper()

	def widgetSetup(self):
		self.b1 = self.startTest()
		self.b2 = self.stop()
		self.b3 = self.liveReading()
		self.b4 = self.clear()
		self.b5 = self.stepper_eb()
		self.b6 = self.stepper_rb()
		self.b7 = self.valve_op()
		self.b8 = self.valve_cl()
		self.b9 = self.pumpOn()
		self.b10 = self.pumpOff()
		self.b11 = self.setBaselineButton()
		self.b12 = self.stepperRightButton()
		self.b13 = self.stepperLeftButton()
		self.b14 = self.stepperZeroButton()
		self.b15 = self.purge()

		self.b1.clicked.connect(lambda: self.fn_startTest())
		self.b2.clicked.connect(lambda: self.fn_stop())
		self.b3.clicked.connect(lambda: self.fn_live())
		self.b4.clicked.connect(lambda: self.fn_clear())
		self.b5.clicked.connect(lambda: self.stepper.expose())
		self.b6.clicked.connect(lambda: self.stepper.recover())
		self.b7.clicked.connect(lambda: self.fn_valve(True))
		self.b8.clicked.connect(lambda: self.fn_valve(False))
		self.b9.clicked.connect(lambda: self.fn_pump(True))
		self.b10.clicked.connect(lambda: self.fn_pump(False))
		self.b11.clicked.connect(lambda: self.fn_setBaseline())
		self.b12.clicked.connect(lambda: self.stepperA.move(5))
		self.b13.clicked.connect(lambda: self.stepperA.move(-5))
		self.b14.clicked.connect(lambda: self.stepper.zero())
		self.b15.clicked.connect(lambda: self.fn_purge())

		self.testKey = False
		self.purgeKey = False
		self.liveKey = False
		self.sampleKey = False

	def fn_startTest(self):
		self.testKey = True
		self.timeVector = [0]
		self.sensor1Vector = [self.sensor1.read()]
		self.sensor2Vector = [self.sensor2.read()]
		self.plot.setData(self.timeVector, self.sensor1Vector)
		self.plot2.setData(self.timeVector, self.sensor2Vector)

		self.fn_clear()

		self.purgeMsg = self.showMessage("Click Ok to start Purge, Cancel to skip")
		if self.purgeMsg == QMessageBox.Ok:
			self.fn_purge()

		self.sampleMsg = self.showMessage("Click Ok to start Sample Collection, Cancel to skip")
		if self.sampleMsg == QMessageBox.Ok:
			self.fn_sampleCollect()

		def endTest():
			self.testKey = False

		def collect_data():
			self.timeVector.append(self.timeVector[-1]+ 0.1)
			self.sensor1Vector.append(self.sensor1.read())
			self.sensor2Vector.append(self.sensor2.read())

		def updateGraph():
			self.plot.setData(self.timeVector, self.sensor1Vector)
			self.plot2.setData(self.timeVector, self.sensor2Vector)

		QTimer.singleshot(self.endTestTime, lambda: endTest())
		QTimer.singleshot(self.startExposeTime, lambda: self.stepper.expose())
		QTimer.singleShot(self.startRecoverTime, lambda: self.stepper.recover())

		self.dataTimer = QTimer()
		self.dataTimer.timeout.connect(lambda: collect_data())
		self.dataTimer.start(100)

		self.graphTimer = QTimer()
		self.graphTimer.timeout.connect(lambda: updateGraph())
		self.graphTimer.start(500)

		while self.testKey:
			app.processEvents()

		self.dataTimer.stop()
		self.graphTimer.stop()

		self.minArray = min([len(self.timeVector), len(self.sensor1Vector), len(self.sensor2Vector)])
		self.dataArray = [self.timeVector[0:self.minArray,], self.sensor1Vector[0:self.minArray,], self.sensor2Vector[0:self.minArray,]]

		self.saveMsg = self.showMessage("Click Ok to Save File, Cancel to skip")
		if self.saveMsg == QMessageBox.Ok:
			filename = "data/{}.csv".format(datetime.now().strftime('%Y_%m_%d_%H%M%S'))
			np.savetxt(filename, self.dataArray, fmt='%.10f', delimiter=',')

		self.purgeMsg = self.showMessage("Click Ok to start Purge, Cancel to skip")
		if self.purgeMsg == QMessageBox.Ok:
			self.fn_purge()

	def fn_live(self):
		self.fn_clear()
		self.liveKey = True
		self.timeVector = list(range(200))
		self.sensor1Vector = [0 for _ in range(200)]
		self.sensor2Vector = [0 for _ in range(200)]

		self.plot.setData(self.timeVector, self.sensor1Vector)
		self.plot2.setData(self.timeVector, self.sensor2Vector)

		def collect_data():
			self.sensor1Vector = self.sensor1Vector[1:]
			self.sensor2Vector = self.sensor2Vector[1:]
			self.sensor1Vector.append(self.sensor1.read())
			self.sensor2Vector.append(self.sensor2.read())

		def updateGraph():
			self.plot.setData(self.timeVector, self.sensor1Vector)
			self.plot2.setData(self.timeVector, self.sensor2Vector)

		self.dataTimer = QTimer()
		self.dataTimer.timeout.connect(lambda: collect_data())
		self.dataTimer.start(100)

		self.graphTimer = QTimer()
		self.graphTimer.timeout.connect(lambda: updateGraph())
		self.graphTimer.start(500)

		while self.liveKey:
			app.processEvents()

		self.dataTimer.stop()
		self.graphTimer.stop()

	def fn_stop(self):
		self.testKey = False
		self.purgeKey = False
		self.liveKey = False
		self.sampleKey = False

		self.fn_valve(False)
		self.fn_pump(False)

	def fn_clear(self):
		self.timeVector = []
		self.sensor1Vector = []
		self.sensor2Vector = []
		self.minArray = []
		self.dataArray = []
		self.plot.setData(self.timeVector, self.sensor1Vector)
		self.plot2.setData(self.timeVector, self.sensor2Vector)

	def fn_valve(self, status):
		if status:
			self.kit.motor3.throttle = 1
		elif not status:
			self.kit.motor3.throttle = 0
		else:
			self.kit.motor3.throttle = 0

	def fn_pump(self, status):
		if status:
			self.kit.motor4.throttle = 1
		elif not status:
			self.kit.motor4.throttle = 0
		else:
			self.kit.motor4.throttle = 0

	def fn_setBaseline(self):
		pass

	def fn_purge(self):
		self.purgeKey = True
		self.fn_valve(True)
		self.fn_pump(True)

		def endPurge():
			self.purgeKey = False

		QTimer.singleshot(self.purgeTotalTime, lambda: endPurge())
		QTimer.singleshot(self.purgeMCTime, lambda: self.stepper_eb())

		while self.purgeKey:
			app.processEvents()

		self.stepper_rb()
		self.fn_valve(False)
		self.fn_pump(False)

	def sampleCollect(self):
		self.sampleKey = True
		self.fn_valve(True)
		self.fn_pump(True)

		def endSampleCollect():
			self.sampleKey = False

		QTimer.singleShot(self.sampleStopTime, lambda: endSampleCollect())

		while self.sampleKey:
			app.processEvents()

		self.fn_valve(False)
		self.fn_pump(False)

	def showMessage(self, text):
		self.msg = QMessageBox()
		self.msg.setIcon(QMessageBox.Information)
		self.msg.setText(text)
		self.msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
		return self.msg.exec_()


	def uiSetup(self):
		self.layout = QGridLayout()
		self.graph = self.Graph()
		self.plot = self.graph.plot(self.timeVector, self.sensor1Vector, pen='#800020', name='INTERNAL')
		self.plot2 = self.graph.plot(self.timeVector, self.sensor2Vector, pen='#186285', name='EXTERNAL')
		self.graph.setYRange(0, 5)

		self.layout.addWidget(self.graph, 0, 0, 5, 5)
		self.layout.addWidget(self.b1, 6, 0, 1, 1)
		self.layout.addWidget(self.b2, 7, 0, 1, 1)
		self.layout.addWidget(self.b3, 6, 1, 1, 1)
		self.layout.addWidget(self.b4, 7, 1, 1, 1)
		self.layout.addWidget(self.b5, 6, 2, 1, 1)
		self.layout.addWidget(self.b6, 7, 2, 1, 1)
		self.layout.addWidget(self.b7, 6, 3, 1, 1)
		self.layout.addWidget(self.b8, 7, 3, 1, 1)
		self.layout.addWidget(self.b9, 6, 4, 1, 1)
		self.layout.addWidget(self.b10, 7, 4, 1, 1)
		self.layout.addWidget(self.b11, 6, 5, 1, 1)
		self.layout.addWidget(self.b12, 2, 5, 1, 1)
		self.layout.addWidget(self.b13, 3, 5, 1, 1)
		self.layout.addWidget(self.b14, 4, 5, 1, 1)
		self.layout.addWidget(self.b15, 7, 5, 1, 1)

		self.setLayout(self.layout)


def main():
	window = mainWindow()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
