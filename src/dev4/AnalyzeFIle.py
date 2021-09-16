import pickle5 as pickle
import pandas as pd

def analyze(file):
	clfFile = open('classifier.obj', 'rb')
	clf = pickle.load(clfFile)
	clfVal = clf.predict(file)
	print(clfVal)

def loadFile(filename):
	data = pd.read_csv("{}".format(filename), delimiter=',')
	myarray = data.values
	myarray = myarray[1, 0:3900]
	analyze(myarray)

if __name__ == "__main__":
	myfile = "../DEV_v3/data/d4v3_m0.0_e50.0_0912163405.csv"
	loadFile(myfile)
