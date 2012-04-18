#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import math
import pylab

# Find a JSON parser
try:
	import json
    # import simplejson as json    
except ImportError:
    try:
    	import simplejson as json
        # import json
    except ImportError:
    	print 'ERROR: JSON parser not found!'

class ROCpt():

	def __init__(self, tp, fp, tn, fn, label=''):
		
		self.tp = float(tp)
		self.fp = float(fp)
		self.tn = float(tn)
		self.fn = float(fn)
		self.label = label

	def positives(self):

		return self.tp + self.fn

	def negatives(self):

		return self.fp + self.tn

	# true positives rate
	def tp_rate(self):

		return self.tp / self.positives()

	# false positives rate
	def fp_rate(self):

		return self.fp / self.negatives()

	def precision(self):

		return self.tp / (self.tp + self.fp)

	def recall(self):

		return self.tp / self.positives()

	def accuracy(self):

		return self.tp / (self.tp + self.fp)

	def f_measure(self):

		return 2.0 / (1/self.precision() + 1/self.recall())

class ROCPlot():
	def __init__(self, fig_title='ROC-graph', filename=None):

		pylab.figure(figsize=(10,10))		
		pylab.suptitle(fig_title, fontsize=16)
		pylab.plot([0,1],[0,1], ":k")
		pylab.axis([0,1,0,1])  
		pylab.xlabel('False positive rate.')
		pylab.ylabel('True positive rate.')
		pylab.grid(True)

		if filename:
			f = open(filename,'r')
			content = f.read()
			content = json.loads(content)		
			f.close()

			data = content.get('data')

			def extract(x):
				return ROCpt(x.get('tp'), x.get('fp'), x.get('tn'), x.get('fn'), label=x.get('label', ''))
			rocpts = [extract(x) for x in data]
			for rocpt in rocpts:
				self.plot(rocpt)
			self.show()

	def show(self):
		
		pylab.legend()
		pylab.show()

	def plot(self, rocpt):

		pylab.plot(rocpt.fp_rate(), rocpt.tp_rate(),"or", label=rocpt.label)


	def generate_file(self, filename, data):

		content = json.dumps(dict(data=[dict(tp=tp,fp=fp,tn=tn,fn=fn,label=label) for tp, fp, tn, fn, label in data]))
		f = open(filename,'w')
		f.write(content)
		f.close()		

	def help(self):

		help_txt =  """
	# below are various ways to use the ROCPlot class

	roc_plot = ROCPlot()
	# define a number of points in ROC-space	
	rocpts = [ROCpt(12,2,13,2), ROCpt(22,6,7,3), ROCpt(22,3,14,7)]	
	# plot each point
	for rocpt in rocpts:
		roc_plot.plot(rocpt)
	# when done plotting points tell ROCPlot to show the final figure
	roc_plot.show()	

	# a data-file can be generated
	data = [(2,1,4,2),(6,2,5,1)]
	roc_plot.generate_file('roc_data.txt', data)

	# one can also load data from a filename
	roc_plot = ROCPlot(filename='roc_data.txt')
		"""
		print help_txt

def main():

	roc_plot = ROCPlot()
	data = [(2,1,4,2,'A'),(6,2,5,1,'B')]
	roc_plot.generate_file('roc_data.txt', data)

	roc_plot = ROCPlot(filename='roc_data.txt')

if __name__ == '__main__':
    main()