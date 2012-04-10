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

help_message = '''
USAGE: tweak.py <video_source> <'lauge' or 'anders'>'''

def main():

	videoIDs = ['0Hwpd-tuD7o', '8vF9jGwNPQM', 'fFsAgFx8VzE_part006', 'gbZl6ULwBTU_part020', 'video1', 'video2', 'video3', 'video4', 'video5']

	try:
		arg1 = sys.argv[1]
		if arg1 == '-?':
			print help_message
			return
	except:		
		print help_message
		return


	errors = []
	for thisID in videoIDs:

		metadata_filename = './Tweak/' + thisID + '.m4v_metadata.txt'
		answer_filename = './Tweak/' + thisID + '.m4v.txt'
		metadata_exists = os.path.isfile(metadata_filename)
		answer_exists = os.path.isfile(answer_filename)

		if not metadata_exists:
			print 'Metadata for ' + thisID + ' does not exists'
		if not answer_exists:
			print 'Answer-file for ' + thisID + ' does not exists'

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
			else:
				return

			answer_states = answer_data.get('states')

			# Calculate error
			error = calcErr.simpleCompare(frame_states, answer_states)
			total = error.get('total')
			correct = error.get('correct')
			errors.append(float(correct)/total)
			print thisID + ' correctness: ' + str(float(correct)/total)

	print 'Overall correctness: ' + str(sum(errors)/len(errors))



if __name__ == '__main__':
    main()