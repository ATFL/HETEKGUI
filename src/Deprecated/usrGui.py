import numpy as np
import os
import sys
import time
import csv
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from datetime import datetime
from pandas import read_csv as rc
import pyqtgraph as pg
import RPi.GPIO as GPIO
import Adafruit_ADS1x15 as ads

GPIO.setmode(GPIO.BOARD)
adc1 = ads.ADS1115(0x48)
adc2 = ads.ADS1115(0x48)

# global bg_color
bg_color = '#484848'
thc_neg_color = '#00FF33'
thc_pos_color = '#FF0033'
thc_status = False
# The following are required Global Variables #
global idVal
global filename
global directory
global all_data
all_data = []
idVal = 0
filename = ''
directory = ''

pTime1 = 2 # Pre-purge: this will normally run for 60 seconds
pTime2 = 2 # Pre-purge: this will normally run for 30 seconds
pTime3 = 2 # Pre-purge: this is commented out
pTime4 = 2 # Post-purge: this will normally run for 40 seconds

totTime = 20 # This is the total time: normally 300 seconds
tTime1 = 5 # This is the time when the sensor is extended: Normally 10
tTime2 = 10 # This is the time when the sensor is retracted: Normally 60

w = 320
h = 240

logoScale = 25

app = QApplication(sys.argv)

sens1name = '2602'
sens2name = '2603'
sens3name = '2610'

run_time = []
sens1 = []
sens2 = []
sens3 = []

prm_list = rc('parameters.csv', delimiter=',', header='infer')
sVersion = prm_list['Software Version'].values
dVersion = prm_list['Device Version'].values
dID = prm_list['Device ID'].values

curdir = os.getcwd()


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


class LinearActuator:
    def __init__(self, pinLA, pinEnable):
        self.pinLA = pinLA
        self.pinEnable = pinEnable
        GPIO.setup(self.pinLA, GPIO.OUT)
        GPIO.setup(self.pinEnable, GPIO.OUT)
        GPIO.output(self.pinEnable, GPIO.HIGH)
        self.pwm = GPIO.PWM(pinLA, 50)
        self.pwm.start(8.5)
        QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
        self.state = 'r'

    def extend(self):
        # print('Extending linear actuator.')
        GPIO.output(self.pinEnable, GPIO.HIGH)
        extending = 5.3  # 5.3
        self.pwm.ChangeDutyCycle(extending)
        QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
        self.state = 'e'

    def retract(self):
        # print('Retracting linear actuator.')
        GPIO.output(self.pinEnable, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(8.5)
        QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
        self.state = 'r'

    def default(self):
        # print('Moving linear actuator to default (center) position.')
        GPIO.output(self.pinEnable, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(6)
        QTimer.singleShot(1.5*1000, lambda: GPIO.output(self.pinEnable, GPIO.LOW))
        self.state = 'd'


class Valve:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.state = False

    def switch(self):
        if self.state == False:
            self.enable()
        elif self.state == True:
            self.disable()

    def enable(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.state = True
        print(self.name + ' enabled.')
        # print("GPIO.LOW")

    def disable(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.state = False
        print(self.name + ' disabled.')

# Initializing the external components


valve1 = Valve("main", 18)
valve1.disable()
valve2 = Valve("main2", 15)
valve2.disable()
valve3 = Valve("main3", 16)
valve3.disable()

mos1 = MOS(adc1, 0)
mos2 = MOS(adc1, 1)
mos3 = MOS(adc1, 2)
mos4 = MOS(adc1, 3)
mos5 = MOS(adc2, 0)
mos6 = MOS(adc2, 1)
mos7 = MOS(adc2, 2)
mos8 = MOS(adc2, 3)

la = LinearActuator(8, 10)
la.retract()


class Window8(QWidget):
    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window8.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    class newTest(QPushButton):
        def __init__(self, parent=None):
            super(Window8.newTest, self).__init__()
            self.setText('End Test')

    def __init__(self, *args, **kwargs):
        super(Window8, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        if thc_status:
            self.setStyleSheet('background-color: {}'.format(thc_pos_color))
        else:
            self.setStyleSheet('background-color: {}'.format(thc_neg_color))
        layout = QGridLayout()
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        b1 = self.exitButton()
        b2 = self.newTest()
        b2.clicked.connect(lambda: self.startNewTest())
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(b1)
        layout.addWidget(b2)
        self.setLayout(layout)

    def startNewTest(self):
        run_time = []
        sens1 = []
        sens2 = []
        sens3 = []
        thc_status = False
        self.window1()

    def window1(self):
        self.w1 = Window1()
        self.w1.show()
        self.close()


class Window7(QWidget):
    # This window shows the graph of the test, just for reference
    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window7.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    class nextButton(QPushButton):
        def __init__(self, parent=None):
            super(Window7.nextButton, self).__init__()
            self.setText('Next')

    class Graph(pg.PlotWidget):
        def __init__(self, parent=None):
            super(Window7.graph, self).__init__()
            self.setStyleSheet("pg.PlotWidget {border-style: outset; max-height: 50}")

    def __init__(self, *args, **kwargs):
        super(Window7, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        self.graph = self.Graph()
        self.plotGraph()
        self.mlResults()
        self.postPurge1()
        self.b1 = self.exitButton()
        self.b2 = self.nextButton()
        # self.b2.setDisabled() # WILL FIX THIS EVENTUALLY
        self.b2.clicked.connect(lambda: self.window8())
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(self.graph, 2, 0, 3, 3)
        layout.addWidget(self.b1, 0, 2, 1, 1)
        layout.addWidget(self.b2, 1, 2, 1, 1)
        self.setLayout(layout)

    def plotGraph(self):
        self.graph.plot(run_time, sens1, pen='r', name='{}'.format(sens1name))
        self.graph.plot(run_time, sens2, pen='g', name='{}'.format(sens2name))
        self.graph.plot(run_time, sens3, pen='b', name='{}'.format(sens3name))

    def mlResults(self):
        print('Doing ML')
        thc_status = True
        # SamplesPerSecond = 10
        # import dill
        # dillfile = 'Model.sav'
        # p = dill.load(open(dillfile,'rb'))
        # data = p(all_data)
        # print(data)
        # if data == 'THC Detected':
        #     thc_status = True
        # else:
        #     thc_status = False

    def postPurge1(self):
        QTimer.singleShot(pTime4, lambda: self.postPurge2)
        la.default()
        valve1.enable()
        valve2.enable()
        valve3.enable()

    def postPurge2(self):
        la.retract()
        valve1.disable()
        valve2.disable()
        valve3.disable()
        # self.b2.setEnabled(s) # WILL FIX THIS EVENTUALLY

    def window8(self):
        self.w8 = Window8()
        self.w8.show()
        self.close()


class Window6(QWidget):
    # This page will show a progress bar, and say testing in progress
    # NOTES: page is done building, requires code work to collect data. Should also save data after collection.
    # NOTES: Data collection and saving is done for sens1, sens2, sens3.
    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window6.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window6, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Test in Progress')
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(label)
        self.pgBar = QProgressBar(self)
        # self.pgBar.setGeometry()
        self.pgBar.setMaximum(totTime)
        self.pgBar.setValue(0)
        layout.addWidget(self.pgBar)
        self.setLayout(layout)
        self.runTest()

    def runTest(self):
        print('Testing')
        self.aVal = 0
        la.retract()
        valve1.disable()
        valve2.disable()
        valve3.disable()
        startTime = time.time()
        print('STEP 1: setting up components')

        def saveData(data):
            global directory
            np.savetxt('{}/{}_id{}.csv'.format(directory, datetime.now().strftime('%Y_%m_%d_%H%M%S'), idVal), data, fmt='%.10f', delimiter=',')
            print('File Saved')

        def updatePG():
            self.pgBar.setValue(self.aVal)
            self.aVal += 1
            print('Updating PG, val: {}'.format(self.aVal))

        def updateData():
            run_time.append(time.time() - startTime)
            sens1.append(mos1.read())
            sens2.append(mos2.read())
            sens3.append(mos3.read())

        def endTest():
            pgTimer.stop()
            dataTimer.stop()
            print('Stopping Timers')
            global all_data
            all_data = np.column_stack((run_time, sens1, sens2, sens3))
            saveData(all_data)
            print('Data Collection Complete, Moving to ML')
            self.window7()

        QTimer.singleShot(tTime1*1000, lambda: la.extend())
        QTimer.singleShot(tTime2*1000, lambda: la.retract())
        QTimer.singleShot(totTime*1000, lambda: endTest())
        pgTimer = QTimer()
        pgTimer.timeout.connect(lambda: updatePG())
        print('STEP2: created pgTimer')
        dataTimer = QTimer()
        dataTimer.timeout.connect(lambda: updateData())
        print('STEP3: created DataTimer')

        print('STEP4: Single Shot Timers started')
        dataTimer.start(100)
        pgTimer.start(1000)


    def window7(self):
        self.w7 = Window7()
        self.w7.show()
        self.close()


class Window5(QWidget):
    # This page says blow in and has a button to click once done
    # NOTES: This page is done building, needs placement work
    class button1(QPushButton):
        def __init__(self, parent=None):
            super(Window5.button1, self).__init__()
            self.setText('Click Once Ready')

    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window5.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window5, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Blow In')
        b1 = self.button1()
        b1.clicked.connect(lambda: self.window6())
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(label)
        layout.addWidget(b1)
        self.setLayout(layout)

    def window6(self):
        self.w6 = Window6()
        self.w6.show()
        self.close()


class Window4(QWidget):
    # This page shows up for pre test purging
    # NOTES: This page requires the code for adding the purging.
    # NOTES: Purging code is finished, building is done, needs placement work.
    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window5.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window4, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def purge3(self):
        print('This is purge 3')
        self.cVal = 0
        self.pgBar.setMaximum(pTime3)
        self.pgBar.setValue(0)

        la.default()
        valve1.enable()
        valve2.enable()
        valve3.enable()

        def updatePG3():
            self.pgBar.setValue(self.cVal)
            self.cVal += 1
            print('Updating PG, val: {}'.format(self.cVal))
            if self.cVal == (pTime3 + 1):
                timer4.stop()

                valve1.disable()
                valve2.disable()
                valve3.disable()
                la.retract()

                print('Moving to testing')
                self.window5()

            timer4 = QTimer()
            timer4.timeout.connect(lambda: updatePG3())
            timer4.start(1000)

    def purge2(self):
        print('This is purge 2')
        self.bVal = 0
        self.pgBar.setMaximum(pTime2)
        self.pgBar.setValue(0)

        la.extend()
        valve2.enable()
        valve3.enable()

        def updatePG2():
            self.pgBar.setValue(self.bVal)
            self.bVal += 1
            print('Updating PG, val: {}'.format(self.bVal))
            if self.bVal == (pTime2 + 1):
                timer3.stop()
                # timer3.killTimer()
                valve1.disable()
                valve2.disable()
                valve3.disable()
                la.retract()
                print('Moving to Purge 3')
                self.window5()

        timer3 = QTimer()
        timer3.timeout.connect(lambda: updatePG2())
        timer3.start(1000)

    def purge1(self):
        # This is the first purge. It will open Valve 1, linear actuator is retracted
        self.aVal = 0
        self.pgBar.setMaximum(pTime1)
        self.pgBar.setValue(0)

        valve1.enable()
        valve2.disable()
        valve3.disable()
        la.retract()

        def updatePG():
            self.pgBar.setValue(self.aVal)
            self.aVal += 1
            print('Updating PG, val: {}'.format(self.aVal))
            if self.aVal == (pTime1 + 1):
                timer2.stop()
                #timer2.killTimer()
                valve1.disable()
                print('Moving to step 2')
                self.purge2()

        timer2 = QTimer()
        timer2.timeout.connect(lambda: updatePG())
        timer2.start(1000)

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Purging ...')
        self.pgBar = QProgressBar(self)
        # self.pgBar.setGeometry()
        self.pgBar.setMaximum(pTime1)
        self.pgBar.setValue(0)
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(label)
        layout.addWidget(self.pgBar)
        self.purge1()

    def window5(self):
        self.w5 = Window5()
        self.w5.show()
        self.close()


class Window3(QWidget):
    # This Page will Start the procedure
    # NOTES: This page is done building, requiers some placement work.
    class startButton(QPushButton):
        def __init__(self, parent=None):
            super(Window3.startButton, self).__init__()
            self.setText('Start Test')

    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window3.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window3, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Ready')
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        b1 = self.startButton()
        b2 = self.exitButton()
        b1.clicked.connect(lambda: self.window4())
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(label)
        layout.addWidget(b1)
        layout.addWidget(b2)
        self.setLayout(layout)

    def window4(self):
        self.w4 = Window4()
        self.w4.show()
        self.close()


class lsWindow(QWidget):
    # This page handles the new window for loading a subject
    # Might change the spinbox to a slider. But otherwise, done.
    class selectButton(QPushButton):
        def __init__(self, parent=None):
            super(lsWindow.selectButton, self).__init__()
            self.setText('Select')

    class cancelButton(QPushButton):
        def __init__(self, parent=None):
            super(lsWindow.cancelButton, self).__init__()
            self.setText('Cancel')

    def __init__(self, *args, **kwargs):
        super(lsWindow, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        self.qsbox = QSpinBox()
        self.qsbox.setRange(1,100)
        b1 = self.selectButton()
        b2 = self.cancelButton()
        b1.clicked.connect(lambda: self.window3())
        b2.clicked.connect(lambda: self.window2())
        layout.addWidget(self.qsbox)
        layout.addWidget(b1)
        layout.addWidget(b2)
        self.setLayout(layout)

    def window3(self):
        idCheck = self.qsbox.value()
        myArray = np.genfromtxt('idDatabase.csv', delimiter=',', skip_header=1)
        col1 = myArray[:, 0]
        check = np.isin(idCheck, col1, assume_unique=True)
        if check:
            global idVal
            idVal = idCheck
            global directory
            print('Loading subject {}'.format(idVal))
            directory = 'Data/byID/id{}'.format(idVal)
            self.w3 = Window3()
            self.w3.show()
            self.close()
        else:
            self.window2()

    def window2(self):
        self.w2 = Window2()
        self.w2.show()
        self.close()


class Window2(QWidget):
    # This is the User ID Page
    # NOTES: This page is done building, requires placement work.
    class NewSubject(QPushButton):
        def __init__(self, parent=None):
            super(Window2.NewSubject, self).__init__()
            self.setText('Add New Subject')
            self.clicked.connect(lambda: self.nsfcn())

        def nsfcn(self):
            print('New Subject')
            self.subNumber = self.genSubNumber()
            global idVal
            idVal = self.subNumber
            print(idVal)
            self.genSubject()

        def genSubNumber(self):
            myArray = np.genfromtxt('idDatabase.csv', delimiter=',', skip_header=1)
            col1 = myArray[:, 0]  # This line chooses the id values
            numFound = False
            myRand = 0
            while not numFound:
                myRand = np.random.randint(1, 100, 1)
                check = np.isin(myRand, col1, assume_unique=True)
                if check:
                    pass
                else:
                    numFound = True
            return int(myRand)

        def genSubject(self):
            global filename
            global directory
            filename = 'id{}'.format(str(idVal))
            directory = 'Data/byID/{}'.format(filename)

            if not os.path.exists(directory):
                os.mkdir(directory)

            today = datetime.now().strftime('%d-%m-%Y')
            f = open('{}/{}.txt'.format(directory, filename), 'w+')
            init_message = 'ID Number: {}\nCreated On: ' \
                           '{}\nDevice Version: {}\nSoftware Version: ' \
                           '{}\nDevice ID: {}\n--------------------'.format(str(idVal), datetime.now().strftime('%d-%m-%Y'),
                                                                            dVersion, sVersion, dID)
            f.write(init_message)

            with open('idDatabase.csv', 'a') as g:
                writer = csv.writer(g)
                writer.writerow([])
                writer.writerow([idVal, today, directory, dVersion, dID])

            print('subject {} created'.format(idVal))

    class LoadSubject(QPushButton):
        def __init__(self, parent=None):
            super(Window2.LoadSubject, self).__init__()
            self.setText('Load Subject')

    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window2.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window2, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        label = QLabel('Subject Setup')
        b1 = self.NewSubject()
        b2 = self.LoadSubject()
        b3 = self.exitButton()
        b1.clicked.connect(lambda: self.window3())
        b2.clicked.connect(lambda: self.lswindow())
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(logoScale))
        idlbl = QLabel('id: {}'.format(idVal))
        datelbl = QLabel('{}'.format(datetime.now().strftime('%m/%d/%Y')))
        timelbl = QLabel('{}'.format(datetime.now().strftime('%H:%M')))
        layout.addWidget(idlbl, 0, 0, 1, 1)
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(datelbl, 1, 0, 1, 1)
        layout.addWidget(timelbl, 1, 1, 1, 1)
        layout.addWidget(label, 2, 0, 1, 1)
        layout.addWidget(b1, 3, 0, 1, 1)
        layout.addWidget(b2, 3, 1, 1, 1)
        layout.addWidget(b3, 3, 2, 1, 1)
        self.setLayout(layout)

    def window3(self):
        self.w3 = Window3()
        self.w3.show()
        self.close()

    def lswindow(self):
        self.lsw = lsWindow()
        self.lsw.show()
        self.close()


class Window1(QWidget):
    # This is just a starting page
    # NOTES: This page is done building, needs some work on placement
    class startButton(QPushButton):
        def __init__(self, parent=None):
            super(Window1.startButton, self).__init__()
            self.setText('Start')

    class exitButton(QPushButton):
        def __init__(self, parent=None):
            super(Window1.exitButton, self).__init__()
            self.setText('Exit')
            self.clicked.connect(lambda: QApplication.closeAllWindows())

    def __init__(self, *args, **kwargs):
        super(Window1, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: {}'.format(bg_color))
        self.setGeometry(0, 0, w, h)
        self.UI()

    def UI(self):
        layout = QGridLayout()
        img = QLabel()
        pix = QPixmap('canLogoImg.png')
        img.setPixmap(pix.scaledToWidth(100))
        b1 = self.startButton()
        b2 = self.exitButton()

        b1.clicked.connect(lambda: self.window2())
        layout.addWidget(img, 0, 1, 1, 1)
        layout.addWidget(b1, 1, 0, 1, 3)
        layout.addWidget(b2, 2, 0, 1, 3)
        self.setLayout(layout)

    def window2(self):
        self.w2 = Window2()
        self.w2.show()
        self.close()


def main():
    win = Window1()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

