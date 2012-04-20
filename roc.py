#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import math
import pylab
import time
import datetime

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

		return self.tp_rate()

	def accuracy(self):

		return self.tp / (self.tp + self.fp)

	def f_measure(self):

		return 2.0 / (1/self.precision() + 1/self.recall())

class ROCPlot():
	def __init__(self, fig_title='ROC-graph', filename=None, show_legend=True, plot_on=True):

		self.show_legend = show_legend
		self.plot_on = plot_on

		if self.plot_on:
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
		
		if self.plot_on:
			if self.show_legend:
				pylab.legend(loc='best')
			pylab.show()

	def plot(self, rocpt):

		if self.plot_on:
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

import tweak2
import threading
import Queue
from multiprocessing import Process, Pipe

class Worker(threading.Thread):

	def __init__(self, in_queue, out_queue, method):
		threading.Thread.__init__(self)

		self.label = str(method.__name__)
		self.tweak = tweak2.Tweak(method)
		self.in_queue = in_queue
		self.out_queue = out_queue

	def run(self):

		while True:

			#grabs parameter from queue
			p = self.in_queue.get()

			tp,fp,tn,fn = self.tweak.tweak(p)	
			label = self.label

			result = tp,fp,tn,fn, label
			self.out_queue.put(result, block=False)

			#signals to queue job is done
			self.in_queue.task_done()

class Gatherer(threading.Thread):

	def __init__(self, in_queue, num_results, filename):
		threading.Thread.__init__(self)

		self.in_queue = in_queue
		self.num_results = num_results
		self.filename = filename
		self.data = []

	def run(self):

		# stop = False
		while True:

			#grabs result from queue and append to data
			result = self.in_queue.get()
			self.data.append(result)
			
			print '%d, %d' % (len(self.data), self.num_results)

			if len(self.data) == self.num_results:
				# stop = True
				roc_plot = ROCPlot(plot_on=False)
				roc_plot.generate_file(self.filename, self.data)

			#signals to queue job is done
			self.in_queue.task_done()

def main():

	# roc_plot = ROCPlot()
	# data = [(2,1,4,2,'A'),(6,2,5,1,'B')]
	# roc_plot.generate_file('roc_data.txt', data)

	# roc_plot = ROCPlot(filename='roc_data.txt')

	# WTF???
	# 16 threads, 16 params: 2:11
	# 4 threads, 16 params: 2:02
	# 2 threads, 16 params: 2:07
	# 32 threads, 64 params: 

	filename = 'roc_data2.txt'
	generate_data = True
	if generate_data:
		start = time.time()

		threads = 32
		data = []
		import compute_frame_state	
		method = compute_frame_state.computeFrameStateAnders
		params = np.append(np.linspace(1e-6,0.5,48), np.linspace(0.5+1e-6,1,20))
		params = np.linspace(1e-6,0.5,64)

		print 'generating data with %d threads. #parameters: %d' % (threads, len(params))

		threads = min(threads, len(params))
		in_queue = Queue.Queue()
		out_queue = Queue.Queue()
		#spawn a pool of threads, and pass them queue instance 
		for i in range(threads):
			print 'spawning worker #%d' % i
			t = Worker(in_queue, out_queue, method)
			t.setDaemon(True)
			t.start()

		print 'spawning gatherer'
		t = Gatherer(out_queue, len(params), filename)
		t.setDaemon(True)
		t.start()	

		#populate queue with data   
		for p in params:
			print 'adding: %s(%f)' % (method.__name__, p)
			in_queue.put(p)

		print 'waiting for jobs to complete...'
		#wait on the queue until everything has been processed     
		in_queue.join()
		print 'workers done!'
		out_queue.join()
		print 'gatherer done!'
		print 'Done and done!'

		end = time.time()

		elapsed_time = end - start
		print 'elapsed time: %d:%02d' % (int(elapsed_time/60.0), int(elapsed_time % 60.0))
	

	# params = np.append(np.linspace(1e-6,0.25,20), np.linspace(0.25 + 1e-6,1,15))
	# i = 0	
	# for p in params:
	# 	tp,fp,tn,fn = tweak2.tweak(method, p)
	# 	label = str(method.__name__)
	# 	data.append((tp,fp,tn,fn,label))
		
	# 	i += 1
	# 	print '%2.2f%%' % (100 * float(i)/len(params))
	# roc_plot = ROCPlot(plot_on=False)
	# roc_plot.generate_file(filename, data)

	ROCPlot(filename=filename, show_legend=False)

if __name__ == '__main__':
    main()