import pickle5 as pickle
import pandas as pd

class ML:
	def init__(self, file):
		super(ML, self).__init__()
		self.loadFile(file)

	def analyze(self):
		self.clfFile = open('classifier.obj', 'rb')
		self.clf = pickle.load(self.clfFile)
		self.clfVal = self.clf.predict(self.myarray)
		print(self.clfVal)

	def loadFile(self, filename):
		data = pd.read_csv("data/{}".format(filename), delimiter=',')
		self.myarray = data.values
		self.myarray = self.myarray[1, 0:3900].reshape(1, -1)
		self.analyze(self.myarray)

