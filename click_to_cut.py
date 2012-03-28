#!/usr/bin/env python

import cv2
import cv
import video
from common import anorm2, draw_str
import time
import sys

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

help_message = '''
USAGE: keypress2.py <video_source>'''

def main():
	try:
		video_src = sys.argv[1]
	except:
		print help_message
		return

	cap = video.create_capture(video_src)
	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)

	human_delay = int(60.0 / fps) # 100 ms
	index = 0
	cut_indexes = []
	while True:

		ret, frame = cap.read()
		if ret:
			
			ch = cv2.waitKey(int(1000/fps))

			if ch != -1: # key pressed
				# do cut
				cut_index = max(0, index-human_delay)
				cut_indexes.append(cut_index)
				print 'cut at frame #%d: %2.2f' % (cut_index, cut_index * fps / 1000.0)

			draw_str(frame, (20, 20), 'frame #%d: %2.2f' % (index, index * fps / 1000.0))
			cv2.imshow('', frame)

			index += 1
		else:
			# no more frames...
			break

	part = 0
	capture = cv.CaptureFromFile(video_src)
	fourcc = cv.CV_FOURCC('D','I','V','3') # MPEG-4.3
	width = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
	height =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
	frame_size = (int(width), int(height))
	index = 0
	frame_offset = int(fps/4.0)
	for cut_index in cut_indexes:
		writer = cv.CreateVideoWriter("./cut/%s_part%d.avi" % (video_src.split('.')[-2], part), fourcc, fps, frame_size, 1)
		for i in range(index, cut_index - frame_offset):
			frame = cv.QueryFrame(capture)
			cv.WriteFrame(writer, frame)
			index += 1
		# skip "frame_offset" frames on each side of the cut
		for i in range(index, index + 2 * frame_offset):
			frame = cv.QueryFrame(capture)
			index += 1
		part += 1

if __name__ == '__main__':
    main()