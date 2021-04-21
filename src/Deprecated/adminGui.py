import numpy as np
import os
import sys
import board
import time
import csv
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from datetime import datetime
from pandas import read_csv as rc
import pyqtgraph as pg
import Adafruit_ADS1x15 as ads
from adafruit_motorkit import MotorKit




# VARIABLE SETUP
idVal = 0
appStatus = 'Ready'

app = QApplication(sys.argv)

class MOS:
    def __init__(self, adc, channel):
        self.GAIN = 2 / 3
        self.adc = adc
        self.channel = channel
        self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144

    def read(self):
        self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
        return self.conversion_value
        # global testTime
        # return sin(time.time())*5

    def read_hum(self):
        self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
        self.conversion_value2 = self.conversion_value / 5 * 125 - 12.5
        return self.conversion_value2

    # TODO: make functions to read temp pressure humidity and oxygen
    def read_temp(self):
        self.conversion_value = (self.adc.read_adc(self.channel, gain=self.GAIN) / pow(2, 15)) * 6.144
        self.conversion_value2 = self.conversion_value / 5 * 218.75 - 66.875
        return self.conversion_value2

    def print(self):
        self.read()
        # print("\nReading from MOS: {}".format(self.conversion_value))


# class LinearActuator:
#     def __init__(self, pinLA, pinEnable):
#         self.pinLA = pinLA
#         self.pinEnable = pinEnable
#         GPIO.setup(self.pinLA, GPIO.OUT)
#         GPIO.setup(self.pinEnable, GPIO.OUT)
#         GPIO.output(self.pinEnable, GPIO.HIGH)
#         self.pwm = GPIO.PWM(pinLA, 50)
#         self.pwm.start(8.5)
#         QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
#         self.state = 'r'
#
#     def extend(self):
#         # print('Extending linear actuator.')
#         GPIO.output(self.pinEnable, GPIO.HIGH)
#         extending = 5.3  # 5.3
#         self.pwm.ChangeDutyCycle(extending)
#         QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
#         self.state = 'e'
#
#     def retract(self):
#         # print('Retracting linear actuator.')
#         GPIO.output(self.pinEnable, GPIO.HIGH)
#         self.pwm.ChangeDutyCycle(8.5)
#         QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
#         self.state = 'r'
#
#     def default(self):
#         # print('Moving linear actuator to default (center) position.')
#         GPIO.output(self.pinEnable, GPIO.HIGH)
#         self.pwm.ChangeDutyCycle(6)
#         QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
#         self.state = 'd'


# class Valve:
#     def __init__(self, name, pin):
#         self.name = name
#         self.pin = pin
#         GPIO.setup(self.pin, GPIO.OUT)
#         GPIO.output(self.pin, GPIO.LOW)
#         self.state = False
#
#     def switch(self):
#         if self.state == False:
#             self.enable()
#         elif self.state == True:
#             self.disable()
#
#     def enable(self):
#         GPIO.output(self.pin, GPIO.HIGH)
#         self.state = True
#         print(self.name + ' enabled.')
#         # print("GPIO.LOW")
#
#     def disable(self):
#         GPIO.output(self.pin, GPIO.LOW)
#         self.state = False
#         print(self.name + ' disabled.')





class Frontpage(QWidget):
    class Graph(pg.PlotWidget):
        def __init__(self, parent=None):
            super(Frontpage.Graph, self).__init__()
            self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

    class startTest(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.startTest, self).__init__()
            self.setText('Start Test')

    class stop(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.stop, self).__init__()
            self.setText('Stop')

    class liveReading(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.liveReading, self).__init__()
            self.setText('Live Reading')

    class clear(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.clear, self).__init__()
            self.setText('Clear All')

    class linac_eb(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.linac_eb, self).__init__()
            self.setText('Open MC Valve')

    class linac_rb(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.linac_rb, self).__init__()
            self.setText('Close MC Valve')

    class valve_op(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.valve_op, self).__init__()
            self.setText('Open Chamber Valve')

    class valve_cl(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.valve_cl, self).__init__()
            self.setText('Close Chamber Valve')

    class setBaselineButton(QPushButton):
        def __init__(self, parent=None):
            super(Frontpage.setBaselineButton, self).__init__()
            self.setText('Set Baseline')

    def __init__(self, *args, **kwargs):
        super(Frontpage, self).__init__(*args, **kwargs)
        self.pTime1 = 2  # Pre-purge: this will normally run for 60 seconds
        self.pTime2 = 2  # Pre-purge: this will normally run for 30 seconds
        self.pTime3 = 2  # Pre-purge: this is commented out
        self.pTime4 = 2  # Post-purge: this will normally run for 40 seconds

        self.totTime = 20  # This is the total time: normally 300 seconds
        self.tTime1 = 5  # This is the time when the sensor is extended: Normally 10
        self.tTime2 = 10  # This is the time when the sensor is retracted: Normally 60
        self.dataRate = 10

        self.tempVal = [] # Full List of temp values over test
        self.pressVal = [] # Full List of pressure values over test
        self.humVal = [] # Full List of humidity values over test
        self.oxVal = [] # Full List of oxygen values over test

        self.tempVal_last = 0 # Last value for the UI
        self.pressVal_last = 0 # Last value for the UI
        self.humVal_last = 0 # Last value for the UI
        self.oxVal_last = 0 # Last value for the UI

        self.setupSystem()
        self.widgetSetup()
        self.UI()

    def setupSystem(self):
        self.kit = MotorKit(i2c=board.I2C())
        self.adc = ads.ADS1115(0x48)
        self.sensor1 = MOS(self.adc, 0)
        self.sensor2 = MOS(self.adc, 1)
        self.kit.motor3.throttle = 0
        self.kit.motor4.throttle = 0

    def widgetSetup(self):
        self.b1 = self.startTest()
        self.b2 = self.stop()
        self.b3 = self.liveReading()
        self.b4 = self.clear()
        self.b5 = self.linac_eb()
        self.b6 = self.linac_rb()
        self.b7 = self.valve_op()
        self.b8 = self.valve_cl()
        self.b9 = self.setBaselineButton()

        self.b1.clicked.connect(lambda: self.fn_startTest())
        self.b2.clicked.connect(lambda: self.fn_stop())
        self.b3.clicked.connect(lambda: self.fn_live())
        self.b4.clicked.connect(lambda: self.fn_clear())
        self.b5.clicked.connect(lambda: self.fn_mcv_open())
        self.b6.clicked.connect(lambda: self.fn_mcv_close())
        self.b7.clicked.connect(lambda: self.fn_cv_open())
        self.b8.clicked.connect(lambda: self.fn_cv_close())
        self.b9.clicked.connect(lambda: self.fn_setBaseline())

        self.ambTemp = QLabel()
        self.ambPressure = QLabel()
        self.ambHumidity = QLabel()
        self.ambTemp.setText('Ambient Temperature is: {}C'.format(self.tempVal_last))
        self.ambPressure.setText('Ambient Pressure is: {}C'.format(self.pressVal_last))
        self.ambHumidity.setText('Ambient Humidity is: {}C'.format(self.humVal_last))
        self.ambTemp.setAlignment(Qt.AlignCenter)
        self.ambPressure.setAlignment(Qt.AlignCenter)
        self.ambHumidity.setAlignment(Qt.AlignCenter)
        self.ambTemp.setFrameShape(QFrame.Box)
        self.ambPressure.setFrameShape(QFrame.Box)
        self.ambHumidity.setFrameShape(QFrame.Box)

    def fn_startTest(self):
        self.fn_clear()
        self.timeVector = np.linspace(0, self.totTime, self.totTime*self.dataRate+1)
        self.sensor1Vector = np.zeros(self.timeVector.shape)
        self.sensor2Vector = np.zeros(self.timeVector.shape)
        self.sampleCounter = 0

        if(self.stepperValve.location != 0):
            self.stepperValve.move(-20)

    def UI(self):
        self.layout = QGridLayout()

        self.appStat = QLabel('Status: {}'.format(appStatus))
        self.appStat.setFrameShape(QFrame.Box)
        self.testTime = QLabel('Baseline Check Time: {}s \n\n'
                               'Exposure Time: {}s \n\nRecovery Time: {}s \n\nTotal Time: {}s'.format(self.tTime1,
                                                                                            self.tTime2 - self.tTime1,
                                                                                            self.totTime - self.tTime2,
                                                                                            self.totTime))

        self.testTime.setFrameShape(QFrame.Box)
        self.vecL = QLabel(
            'Temp: {:d}℃ \n\nHumidity: {:d}% \n\nPressure: {:d}kPa \n\nOxygen: {:d}%'.format(int(self.tempVal_last),
                                                                                             int(self.humVal_last),
                                                                                             int(self.pressVal_last),
                                                                                             int(self.oxVal_last)))
        self.vecL.setFrameShape(QFrame.Box)

        # SET LAYOUT #
        self.layout.addWidget(self.idL, 0, 6, 1, 1)
        self.layout.addWidget(self.appStat, 7, 6, 1, 1)
        self.layout.addWidget(self.vecL, 1, 6, 2, 1)
        self.layout.addWidget(self.testTime, 3, 6, 2, 1)
        self.layout.addWidget(self.Graph(), 1, 0, 4, 4)
        self.layout.addWidget(self.startTest(), 5, 0, 1, 1)
        self.layout.addWidget(self.liveReading(), 6, 0, 1, 1)
        self.layout.addWidget(self.stop(), 5, 1, 1, 1)
        self.layout.addWidget(self.clear(), 6, 1, 1, 1)
        self.layout.addWidget(self.linac_eb(), 5, 2, 1, 1)
        self.layout.addWidget(self.linac_rb(), 6, 2, 1, 1)
        self.layout.addWidget(self.valve_op(), 5, 3, 1, 1)
        self.layout.addWidget(self.valve_cl(), 6, 3, 1, 1)
        self.layout.addWidget(self.setBaselineButton(), 5, 4, 1, 1)

        self.setLayout(self.layout)


# class Subjectpage(QWidget):
#     class load_subject(QPushButton):
#         def __init__(self, parent=None):
#             super(Subjectpage.load_subject, self).__init__()
#             self.setText('Load Subject')
#
#     class new_subject(QPushButton):
#         def __init__(self, parent=None):
#             super(Subjectpage.new_subject, self).__init__()
#             self.setText('New Subject')
#
#     class addLog(QPushButton):
#         def __init__(self, parent=None):
#             super(Subjectpage.addLog, self).__init__()
#             self.setText('Add Log')
#
#     def __init__(self, *args, **kwargs):
#         super(Subjectpage, self).__init__(*args, **kwargs)
#         self.UI()
#
#     def UI(self):
#         self.layout = QGridLayout()
#         self.idL = QLabel('ID: {:d}'.format(idVal))
#         self.idL.setFrameShape(QFrame.Box)
#         self.appStat = QLabel('Status: {}'.format(appStatus))
#         self.appStat.setFrameShape(QFrame.Box)
#
#         self.layout.addWidget(self.idL, 0, 6, 1, 1)
#         self.layout.addWidget(self.appStat, 7, 6, 1, 1)
#         self.layout.addWidget(self.new_subject(), 2, 1, 1, 3)
#         self.layout.addWidget(self.load_subject(), 4, 1, 1, 3)
#         self.layout.addWidget(self.addLog(), 3, 5, 1, 2)
#         self.setLayout(self.layout)


# class Datapage(QWidget):
#     class Graph(pg.PlotWidget):
#         def __init__(self, parent=None):
#             super(Datapage.Graph, self).__init__()
#             self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")
#
#     class clear(QPushButton):
#         def __init__(self, parent=None):
#             super(Datapage.clear, self).__init__()
#             self.setText('Clear')
#
#     class loadData(QPushButton):
#         def __init__(self, parent=None):
#             super(Datapage.loadData, self).__init__()
#             self.setText('Load Data')
#
#     class genReport(QPushButton):
#         def __init__(self, parent=None):
#             super(Datapage.genReport, self).__init__()
#             self.setText('Generate Report')
#
#     def __init__(self, *args, **kwargs):
#         super(Datapage, self).__init__(*args, **kwargs)
#
#         self.pTime1 = 2  # Pre-purge: this will normally run for 60 seconds
#         self.pTime2 = 2  # Pre-purge: this will normally run for 30 seconds
#         self.pTime3 = 2  # Pre-purge: this is commented out
#         self.pTime4 = 2  # Post-purge: this will normally run for 40 seconds
#
#         self.totTime = 20  # This is the total time: normally 300 seconds
#         self.tTime1 = 5  # This is the time when the sensor is extended: Normally 10
#         self.tTime2 = 10  # This is the time when the sensor is retracted: Normally 60
#
#         self.tempVal = []  # Full List of temp values over test
#         self.pressVal = []  # Full List of pressure values over test
#         self.humVal = []  # Full List of humidity values over test
#         self.oxVal = []  # Full List of oxygen values over test
#
#         self.tempVal_last = 0  # Last value for the UI
#         self.pressVal_last = 0  # Last value for the UI
#         self.humVal_last = 0  # Last value for the UI
#         self.oxVal_last = 0  # Last value for the UI
#
#         self.UI()
#
#     def UI(self):
#
#         self.layout = QGridLayout()
#         self.idL = QLabel('ID: {:d}'.format(idVal))
#         self.idL.setFrameShape(QFrame.Box)
#         self.appStat = QLabel('Status: {}'.format(appStatus))
#         self.appStat.setFrameShape(QFrame.Box)
#         self.testTime = QLabel('Baseline Check Time: {}s \n\n'
#                                'Exposure Time: {}s \n\nRecovery Time: {}s \n\nTotal Time: {}s'.format(self.tTime1,
#                                                                                                       self.tTime2 - self.tTime1,
#                                                                                                       self.totTime - self.tTime2,
#                                                                                                       self.totTime))
#
#         self.testTime.setFrameShape(QFrame.Box)
#         self.vecL = QLabel(
#             'Temp: {:d}℃ \n\nHumidity: {:d}% \n\nPressure: {:d}kPa \n\nOxygen: {:d}%'.format(int(self.tempVal_last),
#                                                                                              int(self.humVal_last),
#                                                                                              int(self.pressVal_last),
#                                                                                              int(self.oxVal_last)))
#         self.vecL.setFrameShape(QFrame.Box)
#
#         self.layout.addWidget(self.idL, 0, 6, 1, 1)
#         self.layout.addWidget(self.appStat, 7, 6, 1, 1)
#         self.layout.addWidget(self.vecL, 1, 6, 2, 1)
#         self.layout.addWidget(self.testTime, 3, 6, 2, 1)
#         self.layout.addWidget(self.Graph(), 1, 0, 4, 4)
#         self.layout.addWidget(self.clear(), 6, 1, 1, 1)
#         self.layout.addWidget(self.loadData(), 6, 0, 1, 1)
#         self.layout.addWidget(self.genReport(), 6, 2, 1, 1)
#
#         self.setLayout(self.layout)


class mainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(mainWindow, self).__init__(*args, **kwargs)
        self.UI()

    def UI(self):
        self.layout = QGridLayout()
        tab = QTabWidget()
        tab.addTab(Frontpage(), 'Main')
        # tab.addTab(Subjectpage(), 'Subject')
        # tab.addTab(Datapage(), 'Data Loading')
        self.layout.addWidget(tab)
        self.setLayout(self.layout)


def main():
    window = mainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()