#!/usr/bin/env python

import numpy as np
import numpy
import cv
import cv2
import video
from common import anorm2, draw_str
from time import clock
import math
import sys
import pylab
import os.path

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

DEBUG = False

help_message = '''
USAGE: vid_segmenter.py <video_source> [<show_plot>] [<show_video>]'''

def computeFrameState(magnitudes, contrast):
	
	states = []
	state_values = []
	T = 0.50 # cumulative treshold
	T1 = 0.80 # contrast treshold
	T2 = 0.20 # displacement vector treshold

	# weights
	a = T / T1
	b = T / T2

	for i in range(0,len(magnitudes)):
		state_value = sum([a * contrast[i], b * magnitudes[i]])	
		state_values.append(state_value)		
	states = [v > T for v in state_values]

	return states, state_values
	
def smoothTriangle(data,degree,dropVals=False):
    """performs moving triangle smoothing with a variable degree."""
    """note that if dropVals is False, output length will be identical
    to input length, but with copies of data at the flanking regions"""

    triangle=numpy.array(range(degree)+[degree]+range(degree)[::-1])+1
    smoothed=[]
    for i in range(degree,len(data)-degree*2):
            point=data[i:i+len(triangle)]*triangle
            smoothed.append(sum(point)/sum(triangle))
    if dropVals: return smoothed
    smoothed=[smoothed[0]]*(degree+degree/2)+smoothed
    while len(smoothed)<len(data):smoothed.append(smoothed[-1])
    return smoothed  

def normalize(a, factor=255.0):

	# convert to floating point	
	if not type(a).__name__ == 'numpy.ndarray':
		# a is not a numpy array
		b = np.float64(np.array(a)).copy()
	else:
		b = np.float64(a.copy())
	
	bmin = np.min(b)
	if bmin > 0.0:
		# no point in substracting 0
		b -= np.min(b)

	bmax = np.max(b)
	if bmax > 0.0:
		# to avoid dividing by zero
		b *= factor / bmax
	else:
		return a.copy()

	# convert back to integer
	return b # np.int64(b)

def rms_diff(a,b):
	return rms(a-b)

def rms(a):
	return math.sqrt(np.mean(a**2))

def shift(a,xy):
	# shift matrix and cut off 'excess' columns/rows

	x = xy[0]
	y = xy[1]
	if DEBUG:
		print '(x,y)=(%d,%d)' % (x,y)

	b = a.copy()
	
	if x > 0:
		if DEBUG: print 'shift right'
		b = b[:, 0:-x]
	elif x < 0:
		if DEBUG: print 'shift left'
		b = b[:, -x:]
	if y > 0:
		if DEBUG: print 'shift up'
		b = b[y:, :]
	elif y < 0:
		if DEBUG: print 'shift down'
		b = b[:y, :]

	return b

def getVideoMetadata(video_src, load_video=False):

	cap = video.create_capture(video_src)

	# directions to shift (x,y): down, up, left, right
	directions = [np.array([0,-1]),np.array([0,1]),np.array([-1,0]),np.array([1,0])]

	frames = []
	metadata_filename = video_src + '_metadata.txt'
	metadata_exists = os.path.isfile(metadata_filename)

	# if os.path.isfile(metadata_filename + '.part'):
	# 	print '%s is already processing...' % video_src
	# 	return dict()

	# # "flag" the video as processing
	# if not metadata_exists:		
	# 	f = open(metadata_filename + '.part','w')
	# 	f.close()

	# if metadata is non-existing then we need to load the video anyways
	if not load_video and not metadata_exists:
		print '%s not found, must load video...' % metadata_filename
	load_video = load_video or not metadata_exists
	if load_video:
		print 'loading video: %s' % video_src
		while True:
			ret, frame = cap.read()
			if ret:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				frames.append(frame_gray)
			else:
				break

	# first check if metadata is already on disk
	if metadata_exists:
		# load from file and return that shite!
		f = open(metadata_filename,'r')
		content = f.read()
		d = json.loads(content)		
		# print 'found on disc: ', content
		# print 'loaded as json: ', d
		f.close()
		return d,frames

	shift_vectors = []
	# using a sliding window of 5 frames (avr. of 5 frames)
	shift_vectors_sliding = []
	rmsdiffs = []
	stand_dev = []
	for i in range(0,len(frames)):

		if i % (len(frames) / 10) == 0:
			print '%2.2f%% of %s' % (100 * float(i) / float(len(frames)), video_src)
			
		stand_dev.append(math.sqrt(np.var(frames[i])))
		# for i in range(0,25):
		if len(frames) > 0:
					
			prev_frame = frames[i-1]
			curr_frame = frames[i]

			# global shift offset along the horizontal axis
			x = 0
			# global shift offset along the vertical axis
			y = 0
			# effectively moving 0 pixels in all directions to begin with!
			# oddly enough this seems to be the most prudent choice most of the time
			# lowest_rms_diff = rms_diff(prev_frame, curr_frame)

			# this way the shift is only done if it decrease the error
			# lowest_rms_diff = sys.maxint

			# no reason to normalize?
			prev_frame_normalized = prev_frame #normalize(prev_frame)
			curr_frame_normalized = curr_frame #normalize(curr_frame)

			for spx in [32, 16, 8, 4, 2, 1]:
				
				_x = 0; _y = 0
				# this makes it a greedy algorithm + lowers chance of sinking into a local minima because
				# we are forced to make the shift, even if it increases the error
				lowest_rms_diff = sys.maxint

				# try shifting in all 4 directions
				for d in directions:

					# local shift + global shift
					s = spx * d + np.array([x,y])
					
					# shift previous frame in the opposite direction
					a = shift(prev_frame_normalized, -s)
					b = shift(curr_frame_normalized, s)

					if DEBUG: 
						m,n = curr_frame.shape
						print 'shape of current frame (PRE SHIFT): (%d,%d)' % (m,n)
						m,n = prev_frame.shape
						print 'shape of previous frame (PRE SHIFT): (%d,%d)' % (m,n)					
						m,n = b.shape
						print 'shape of current frame (POST SHIFT): (%d,%d)' % (m,n)				
						m,n = a.shape
						print 'shape of previous frame (POST SHIFT): (%d,%d)' % (m,n)				

					rd = rms_diff(a, b)
					if rd < lowest_rms_diff:
						lowest_rms_diff = rd
						# save best shift including magnitude
						[_x,_y] = spx * d
				# add the local shift to global shift
				x += _x
				y += _y
				if DEBUG: 
					print '(x,y)=(%d,%d), rms = %2.2f' % (x,y,lowest_rms_diff)

			# print 'frame %d: (x,y)=(%d,%d), rms = %2.2f' % (i, x,y,lowest_rms_diff)

			x = int(x)
			y = int(y)
			# x & y are of type numpy.int64 which json cannot parse
			shift_vectors.append((x,y))
			rmsdiffs.append(lowest_rms_diff)
			if len(shift_vectors) < 5:
				shift_vectors_sliding.append((x,y))
			else:
				xs = [x for x,y in shift_vectors[-5:]]
				ys = [y for x,y in shift_vectors[-5:]]
				x = int(sum(xs) / 5.0)
				y = int(sum(ys) / 5.0)
				shift_vectors_sliding.append((x,y))

	d = {'rmsdiffs' : rmsdiffs, 'shift_vectors' : shift_vectors, 'shift_vectors_sliding' : shift_vectors_sliding, 'stand_dev':stand_dev}
	content = json.dumps(d)

	# do not write a file if json parser fails
	if content:
		# write to disc
		f = open(metadata_filename,'w')	
		f.write(content)
		f.close()

	# os.remove(metadata_filename + '.part')

	print '%2d%% of %s' % (100, video_src)

	return d,frames

def main():
	video_src = None
	try:
		arg1 = sys.argv[1]
		if arg1 == '-?':
			print help_message
			return
		else:
			video_src = arg1	
			show_plot = None
			show_video = None
		show_plot = sys.argv[2] == 'true' or sys.argv[2] == 'True'
		show_video = sys.argv[3] == 'true' or sys.argv[3] == 'True'
	except:		
		print 'loading default values'
		if video_src is None:
			print help_message
			return
		if show_plot is None:
			show_plot = True	
		if show_video is None:
			show_video = True

	d,frames = getVideoMetadata(video_src, show_video)

	if not show_video and not show_plot:
		# nothing to see here!
		return

	shift_vectors = d['shift_vectors']
	rmsdiffs = d['rmsdiffs']
	shift_vectors_sliding = d['shift_vectors_sliding']
	stand_dev = d['stand_dev']

	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))

	# degree of smoothness
	degree = 12
	# time in seconds
	t = np.linspace(0, num_frames/fps, len(frames))
	# values are normalized to [0...1]
	# the magnitude of the vector - apply weights according to the direction of the vector? ie. vertical panning is worse than horizontal
	magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
	# a measure of variation/contrast in the frame - a high value indicated less contrast and vice versa
	contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
	# compute if a frame is accepted, and the according value
	frame_states, frame_values = computeFrameState(magnitudes, contrast)

	if show_plot:
		print 'generating plots...'

		pylab.figure(figsize=(10,10))		
		pylab.suptitle(video_src, fontsize=16)

		pylab.subplot(2,2,1, title='displacement vector magnitudes')  
		pylab.plot(t, magnitudes,".k")  
		pylab.plot(t, magnitudes,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')
		pylab.grid(True)

		pylab.subplot(2,2,2, title='frame state values')  
		pylab.plot(t, frame_values,".k")  
		pylab.plot(t, frame_values,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')
		pylab.grid(True)

		pylab.subplot(2,2,3, title='image contrast')
		pylab.plot(t, contrast,".k")  
		pylab.plot(t, contrast,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')
		pylab.grid(True)

		pylab.show()

	if show_video:
		print 'video playback...'

		index = 0
		for frame in frames:
			frame_state = 'BAD' if frame_states[index] else 'GOOD'
			frame_value = frame_values[index]
			draw_str(frame, (20, 20), 'time: %2.1f:%2.1f, magnitude: %2.2f%%, contrast^-1: %2.2f' % (t[index], t[-1], 100 * magnitudes[index], contrast[index]))						
			draw_str(frame, (20, 40), '%s (%2.3f)' % (frame_state, frame_value))

			index += 1
			cv2.imshow('final cut', frame)
			cv2.waitKey(int(1000/fps))

if __name__ == '__main__':
    main()
