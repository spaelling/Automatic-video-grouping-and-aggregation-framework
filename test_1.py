#!/usr/bin/env python

import vid_segmenter as segmenter
import compute_frame_state
import seg_result_comparison as calcErr
import sys
import cv
import cv2
import numpy as np
import math
import os
import json
import pylab
from common import draw_str

smoothTriangle = segmenter.smoothTriangle
getVideoMetadata = segmenter.getVideoMetadata
computeFrameStateAnders = compute_frame_state.computeFrameStateAnders
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge
computeFrameStateNaiive = compute_frame_state.computeFrameStateNaiive
computeFrameStateMagnitudeOnly = compute_frame_state.computeFrameStateMagnitudeOnly
computeFrameStateContrastOnly = compute_frame_state.computeFrameStateContrastOnly

help_message = '''
USAGE: test_1.py <'lauge', 'anders' 'naiive', 'magnitude', 'contrast'> <metadata dir> <answer dir (if any)>'''

def main():

	metadataDir = None
	answerDir = None

	try:
		arg1 = sys.argv[1]
		if arg1 == '-?':
			print help_message
			return
		
		metadataDir = sys.argv[2]
		answerDir = sys.argv[3]
	except:		
		print help_message
		return


	listOfMetaDataFiles = os.listdir(metadataDir)
	
	errors = []
	for metaDataFile in listOfMetaDataFiles:

		thisID = metaDataFile.split('.')[0]

		metadata_filename = metadataDir + '/' + thisID + '.m4v_metadata.txt'
		answer_filename = answerDir + '/' + thisID + '.m4v.txt'

		metadata_exists = os.path.isfile(metadata_filename)
		answer_exists = os.path.isfile(answer_filename)

		if metadata_exists and answer_exists:

			f = open(metadata_filename,'r')
			content = f.read()
			metadata = json.loads(content)
			d = metadata
			f.close()

			f = open(answer_filename,'r')
			content = f.read()
			answer_data = json.loads(content)
			f.close()

			shift_vectors = d['shift_vectors']
			rmsdiffs = d['rmsdiffs']
			shift_vectors_sliding = d['shift_vectors_sliding']
			stand_dev = d['stand_dev']

			# degree of smoothness
			degree = 12
			
			magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
			contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
			
			# compute if a frame is accepted, and the according value
			if arg1 == 'anders':
				frame_states, frame_values = computeFrameStateAnders(magnitudes, contrast)
			elif arg1 == 'lauge':
				frame_states, frame_values = computeFrameStateLauge(magnitudes, contrast)
			elif arg1 == 'naiive':
				frame_states, frame_values = computeFrameStateNaiive(magnitudes, contrast)
			elif arg1 == 'magnitude':
				frame_states, frame_values = computeFrameStateMagnitudeOnly(magnitudes)
			elif arg1 == 'contrast':
				frame_states, frame_values = computeFrameStateContrastOnly(contrast)
			else:
				return

			answer_states = answer_data.get('states')

			# Calculate error
			errors.append(calcErr.simpleCompare(frame_states, answer_states))

	correctRatios = []
	positivePrecisions = []
	positiveRecalls = []
	negativePrecisions = []
	negativeRecalls = []
	
	for error in errors:

		total = error.get('total')
		totalPositives = error.get('total positives')
		totalNegatives = error.get('total negatives')

		correct = error.get('correct')
		incorrect = error.get('incorrect')

		truePositives = error.get('true positives')
		trueNegatives = error.get('true negatives')
		falsePositives = error.get('false positives')
		falseNegatives = error.get('false negatives')

		
		if truePositives + falsePositives > 0:
			positivePrecision = float(truePositives) / (truePositives + falsePositives)
		else:
			positivePrecision = 1.0
		
		if totalPositives > 0:
			positiveRecall = float(truePositives) / totalPositives
		else:
			positiveRecall = 1.0

		if trueNegatives + falseNegatives:
			negativePrecision = float(trueNegatives) / (trueNegatives + falseNegatives)
		else:
			negativePrecision = 1.0

		if totalNegatives > 0:
			negativeRecall = float(trueNegatives) / totalNegatives
		else:
			negativeRecall = 1.0


		correctRatios.append(float(correct)/total)
		positivePrecisions.append(positivePrecision)
		positiveRecalls.append(positiveRecall)
		negativePrecisions.append(negativePrecision)
		negativeRecalls.append(negativeRecall)

	print '\nOverall correctness: %2.3f%%' % (100.0 * (sum(correctRatios)/len(correctRatios)))
	print 'Positive precision: %2.3f%%' % (100.0 * (sum(positivePrecisions)/len(positivePrecisions)))
	print 'Positive recall: %2.3f%%' % (100.0 * (sum(positiveRecalls)/len(positiveRecalls)))
	print 'Negative precision: %2.3f%%' % (100.0 * (sum(negativePrecisions)/len(negativePrecisions)))
	print 'Negative recall: %2.3f%%' % (100.0 * (sum(negativeRecalls)/len(negativeRecalls)))



if __name__ == '__main__':
    main()