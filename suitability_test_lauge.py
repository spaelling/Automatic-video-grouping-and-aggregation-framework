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
    else:
    	print 'JSON parser found'
else:
	print 'JSON parser found'

DEBUG = False

help_message = '''
USAGE: test3.py [<video_source>] [<show_plot>] [<show_video>]'''

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
	b -= np.min(b)
	# normalize values to [0,255]
	b *= factor / np.max(b)

	# convert back to integer
	return np.int64(b)

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
	# if metadata is non-existing then we need to load the video anyways
	if not load_video and not os.path.isfile(video_src + '.txt'):
		print 'metadata not found, must load video...'
	load_video = load_video or not os.path.isfile(video_src + '.txt')
	if load_video:
		print 'loading video: %s...' % video_src
		while True:
			try:
				ret, frame = cap.read()
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				frames.append(frame_gray)
			except:
				print 'Done!'
				break

	# first check if metadata is already on disk
	if os.path.isfile(video_src + '.txt'):
		# load from file and return that shite!
		f = open(video_src + '.txt','r')
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

			prev_frame_normalized = normalize(prev_frame)
			curr_frame_normalized = normalize(curr_frame)

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

			print 'frame %d: (x,y)=(%d,%d), rms = %2.2f' % (i, x,y,lowest_rms_diff)

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
		f = open(video_src + '.txt','w')	
		f.write(content)
		f.close()

	return d,frames

def computeFrameState(magnitudes, contrast):
	
	states = []
	state_values = []
	contrast_lim = 0.80
	magnitudes_lim = 0.20

	for i in range(0,len(magnitudes)):
		state_value = max([contrast[i] * (1 / contrast_lim), magnitudes[i] * (1 / magnitudes_lim)])
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		# state values 
		#state_value = contrast[i] * (1 - contrast_lim) + magnitudes[i] * (1 - magnitudes_lim)
		state_values.append(state_value)


	return states, state_values

def main():
	try:
		print help_message
		video_src = sys.argv[1]
		show_plot = sys.argv[2] == 'true' or sys.argv[2] == 'True'
		show_video = sys.argv[3] == 'true' or sys.argv[3] == 'True'
	except:
		print 'defaulting to default values'
		video_src = "./4J-qtGnNdUk.m4v"
		show_plot = True	
		show_video = True

	d,frames = getVideoMetadata(video_src, show_video)
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
	# a measure of variation/contrast in the frame
	contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
	# compute if a frame is accepted, and the according value
	frame_states, frame_values = computeFrameState(magnitudes, contrast)

	if show_plot:
		print 'generating plots...'

		pylab.figure(figsize=(10,10))
		pylab.suptitle(video_src, fontsize=16)

		vals1 = smoothTriangle(magnitudes, 5)
		pylab.subplot(2,2,1, title='shift vector magnitudes')  
		pylab.plot(t, vals1,".k")  
		pylab.plot(t, vals1,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')

		vals2 = smoothTriangle(frame_values, 5)	
		pylab.subplot(2,2,2, title='frame state values')  
		pylab.plot(t, vals2,".k")  
		pylab.plot(t, vals2,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')

		vals3 = smoothTriangle(contrast, 5)
		pylab.subplot(2,2,3, title='image contrast')
		pylab.plot(t, vals3,".k")  
		pylab.plot(t, vals3,"-k")  
		pylab.axis()  
		pylab.xlabel('secs.')

		pylab.show()

	if show_video:
		print 'video playback...'

		index = 0
		for frame in frames:
			frame_state = 'GOOD' if frame_states[index] else 'BAD'
			frame_value = frame_values[index]
			draw_str(frame, (20, 20), 'time: %2.2fs, magnitude: %2.2f, contrast: %2.2f' % (t[index], magnitudes[index], contrast[index]))						
			draw_str(frame, (20, 40), '%s (%2.3f)' % (frame_state, frame_value))

			index += 1
			cv2.imshow('final cut', frame)
			cv2.waitKey(int(1000/fps))

if __name__ == '__main__':
    main()
