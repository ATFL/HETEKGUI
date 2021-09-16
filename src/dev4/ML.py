import os
import sys
from pathlib import Path
import pickle5 as pickle
import pandas as pd

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

app = QApplication(sys.argv)

class ML:
	def __init__(self, file):
		super(ML, self).__init__()
		self.loadFile(file)

	def analyze(self):
		self.clfFile = open('classifier.obj', 'rb')
		self.clf = pickle.load(self.clfFile)
		self.clfVal = self.clf.predict(self.myarray)
		print(self.clfVal)
		disp = display(self.clfVal)
		disp.show()

	def loadFile(self, filename):
		data = pd.read_csv("{}".format(filename), delimiter=',')
		self.myarray = data.values
		self.myarray = self.myarray[1, 0:3900].reshape(1, -1)
		self.analyze()


class display(QWidget):
	def __init__(self, value):
		super(display, self).__init__()
		self.myLabel = QLabel()
		self.myLabel.setText(str(value))
		self.layout = QGridLayout()
		self.layout.addWidget(self.myLabel)
		self.setLayout(self.layout)


if __name__ == "__main__":
	myFiles = os.listdir("data/")
	paths=sorted(Path("data/").iterdir(), key=os.path.getmtime)
	#print(paths[-1])
	A = ML(paths[-1])