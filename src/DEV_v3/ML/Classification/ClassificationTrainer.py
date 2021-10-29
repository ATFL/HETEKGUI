import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, plot_confusion_matrix
import matplotlib.pyplot as plt
import pickle


class ML:
	def __init__(self, data, targets):
		self.data = pd.read_csv("{}.csv".format(data), delimiter=',')
		self.targets = pd.read_csv("{}.csv".format(targets), delimiter=',')
		self.X = self.data.values[:, 0:3700]
		self.Y = self.targets.values
		self.Y = self.Y.reshape(len(self.Y), )
		self.dataSize = self.data.shape
		self.targetSize = self.targets.shape
		self.num = list(range(self.targetSize[0]))
		print("Data Shape: {}\nTarget Shape: {}".format(self.dataSize, self.targetSize))

	def plotData(self, X, Y):
		plt.figure()
		plt.scatter(X, Y)
		plt.show()

	def split(self, rs):
		self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.Y, test_size=0.3, random_state=rs)
		print("X_Train Shape: {} -- X_Test Shape: {}\nY_Train Shape: {} -- Y_Test Shape: {}".format(self.X_train.shape, self.X_test.shape, self.y_train.shape, self.y_test.shape))
		[self.splitVal1, self.splitVal2] = np.unique(self.y_test, return_counts=True)
		return self.splitVal1, self.splitVal2

	def SVM(self):
		from sklearn.svm import SVC, OneClassSVM
		from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, Normalizer
		from sklearn.pipeline import make_pipeline
		self.clf = make_pipeline(StandardScaler(), SVC())
		self.clf.fit(self.X_train, self.y_train)

	def evaluate(self):
		self.y_predicted = self.clf.predict(self.X_test)
		self.conf = confusion_matrix(self.y_test, self.y_predicted)
		print(self.conf)
		print(self.clf.score(self.X_test, self.y_test))


if __name__ == "__main__":
	A = ML("raw", "targets")
	_1, _2 = A.split(1)
	print(_1, _2)
	A.SVM()
	A.evaluate()
	clfFile = open('classifier.obj', 'wb')
	pickle.dump(A.clf, clfFile)


