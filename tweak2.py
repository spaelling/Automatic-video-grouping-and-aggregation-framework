#!/usr/bin/env python

import seg_result_comparison as calcErr
import numpy as np
import math
import os
import json
import pylab
import vid_segmenter as segmenter
smoothTriangle = segmenter.smoothTriangle

class Tweak():

	def __init__(self, method, path='./Tweak/', smoothness_degree=0):

		self.method = method
		self.path = path
		self.smoothness_degree = smoothness_degree
		self.metadatas = []
		self.answer_datas = []

		self.init()

	def init(self):

		path = self.path

		videoIDs = []
		listOfMetaDataFiles = os.listdir(path)
		for metaDataFile in listOfMetaDataFiles:
			parts = metaDataFile.split('.')
			ID = parts[0]
			kind = parts[1]
			if kind == 'm4v_metadata':
				videoIDs.append(ID)

		f = open('./DataSet/ignore.json','r')
		content = f.read()
		ignore = json.loads(content).get('ignore')

		for thisID in videoIDs:
			# print thisID
			if thisID in ignore:
				# print 'ignoring data in %s' % thisID
				continue

			# uncomment to only use "cut" segments
			# if 'part' not in thisID:
			# 	continue

			metadata_filename = path + thisID + '.m4v_metadata.txt'
			answer_filename = path + thisID + '.m4v.txt'
			metadata_exists = os.path.isfile(metadata_filename)
			answer_exists = os.path.isfile(answer_filename)

			if not metadata_exists:
				print 'Metadata for ' + thisID + ' does not exists'
			# if there is no answer file and the filename does not have 'part' in it
			# it is likely missing. otherwise we will create one
			if not answer_exists and ('part' not in thisID):
				print 'Answer-file for ' + thisID + ' does not exists'	

			# if metadata_exists and answer_exists:
			if metadata_exists:

				f = open(metadata_filename,'r')
				content = f.read()
				metadata = json.loads(content)
				self.metadatas.append(metadata)
				f.close()

			if answer_exists:
				f = open(answer_filename,'r')
				content = f.read()
				answer_data = json.loads(content)
				f.close()
			else:
				answer_data = dict(states=[1 for x in metadata.get('shift_vectors')])
			self.answer_datas.append(answer_data)

	def tweak(self, p):

		errors = []

		for i in range(len(self.metadatas)):

			metadata = self.metadatas[i]
			answer_data = self.answer_datas[i]
			method = self.method

			shift_vectors = metadata['shift_vectors']
			stand_dev = metadata['stand_dev']

			# degree of smoothness
			degree = 12
			
			try:
				magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
				contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
			except IndexError as e:
				# too little data in segment will cause this error
				continue
			
			frame_states, frame_values = method(magnitudes, contrast, p)
			smoothness_degree = self.smoothness_degree
			if smoothness_degree:
				frame_states = [round(x) for x in smoothTriangle(frame_states, smoothness_degree)]
			answer_states = answer_data.get('states')

			# Calculate error
			errors.append(calcErr.simpleCompare(frame_states, answer_states))

		totals = 0
		totalPositives = 0
		totalNegatives = 0
		corrects = 0
		truePositives = 0
		trueNegatives = 0
		falsePositives = 0
		falseNegatives = 0
		
		for error in errors:

			totals += int(error.get('total'))
			totalPositives += int(error.get('total positives'))
			totalNegatives += int(error.get('total negatives'))

			corrects += error.get('correct')

			truePositives += error.get('true positives')
			trueNegatives += error.get('true negatives')
			falsePositives += error.get('false positives')
			falseNegatives += error.get('false negatives')

		correctsRatio = float(corrects)/totals
		try:
			positivePrecision = float(truePositives) / (truePositives + falsePositives)
		except:
			positivePrecision = -1
		try:
			positiveRecall = float(truePositives) / totalPositives
		except:
			positiveRecall = -1
		try:
			negativePrecision = float(trueNegatives) / (trueNegatives + falseNegatives)
		except:
			negativePrecision = -1
		try:
			negativeRecall = float(trueNegatives) / totalNegatives
		except:
			negativeRecall = -1

		return truePositives, falsePositives, trueNegatives, falseNegatives
