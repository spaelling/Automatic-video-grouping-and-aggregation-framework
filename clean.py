#!/usr/bin/python

import os
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
USAGE: clean.py <folder>
'''

def main():
	argv = sys.argv
	try:
		folder = argv[1]
	except:
		print help_message
		return

	f = open('./DataSet/ignore.json','r')
	content = f.read()
	ignore = json.loads(content).get('ignore')
	for filename in ignore:
		# print 'removing %s%s' % (folder, filename)
		os.system('rm %s%s.avi' % (folder, filename))

if __name__ == '__main__':
    main()