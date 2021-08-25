from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from adafruit_motorkit import MotorKit
import sys

app = QApplication(sys.argv)

class MOTOR:
    def __init__(self, channel, name):
        super(MOTOR, self).__init__()
        self.motor = channel
        self.name = name

        self.status = False

    def activate(self):
        try:
            self.motor.throttle = 0.75
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


class ControlPanelWindow(QWidget):
    class button(QPushButton):
        def __init__(self, *args, **kwargs):
            super(ControlPanelWindow.button, self).__init__()
            self.setText("Button Name")

        def setButtonColor(self, color):
            self.setStyleSheet('background-color: {}'.format(color))

        def setButtonText(self, text):
            self.setText(text)

    def __init__(self):
        super(ControlPanelWindow, self).__init__()
        self.loadWindowSettings()
        self.loadComponents()
        self.CPWButtonSetup()
        self.CPWUI()

    def loadWindowSettings(self):
        self.width = 480
        self.height = 320
        self.bg_color = '#484848'
        self.setStyleSheet('background-color: {}'.format(self.bg_color))
        self.setGeometry(0, 0, self.width, self.height)
        print("Window Settings Loaded")

    def loadComponents(self):
        self.kit = MotorKit(0x63)
        self.pump = MOTOR(self.kit.motor4, "Pump")

        self.pump.deactivate()

        print("Components Loaded")

    def CPWButtonSetup(self):
        self.b1 = self.button()
        self.b1.setButtonText("Toggle Pump")
        self.b1.clicked.connect(lambda: self.pump.toggle())

    def CPWUI(self):
        self.layout = QGridLayout()

        self.layout.addWidget(self.b1)

        self.setLayout(self.layout)

def main():
    UI = ControlPanelWindow()
    UI.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()