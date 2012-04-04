#!/usr/bin/python

import json

def sectionCompare(suggestion, answer):

	if len(suggestion) == len(answer) and len(answer) > 1:

		# Build sections from answer
		positiveSections = []
		negativeSections = []
		startIndex = 0
		endIndex = 0
		for i in range(1,len(answer)):
			
			endIndex = i

			if answer[i] != answer[endIndex - 1]:
				
				# Not in same section anymore
				if answer[endIndex - 1] == 0:
					negativeSections.append((startIndex, endIndex))
				else:
					positiveSections.append((startIndex, endIndex))
				startIndex = i

		# Add the last section
		if answer[-1] == 0:
			negativeSections.append((startIndex, endIndex + 1))
		else:
			positiveSections.append((startIndex, endIndex + 1))

		overlap = []

		# Compare all the positive sections with the suggestion
		for (start, end) in positiveSections:
			s = suggestion[start:end]
			overlap.append(float(sum(s)) / len(s))

		# Compare all the positive sections with the suggestion
		for (start, end) in negativeSections:
			s = suggestion[start:end]
			overlap.append(float(len(s) - sum(s)) / len(s))

		print 'OVERLAP: ' + str(float(sum(overlap)) / len(overlap))
	else:
		print 'List must have the same length and contain at least two element'



def simpleCompare(suggestion, answer):

	if len(suggestion) == len(answer):

		truePositives = 0
		trueNegatives = 0
		falsePositives = 0
		falseNegatives = 0

		for i in range(len(suggestion)):
			s = suggestion[i]
			a = answer[i]
			if s == 0:
				if a == 0:
					trueNegatives += 1
				if a == 1:
					falseNegatives += 1
			if s == 1:
				if a == 0:
					falsePositives += 1
				if a == 1:
					truePositives += 1

		correct = truePositives + trueNegatives
		incorrect = falsePositives + falseNegatives
		total = correct + incorrect
		totalPositives = sum(answer)
		totalNegatives = len(answer) - sum(answer)

		return {'total': total, 'total positives': totalPositives, 'total negatives': totalNegatives, 'correct': correct, 'incorrect': incorrect, 'true positives': truePositives, 'true negatives': trueNegatives, 'false positives': falsePositives, 'false negatives': falseNegatives}
	else:
		print 'List must have the same length'
		return {}


def calcError(data):

	total = data.get('total')
	totalPositives = data.get('total positives')
	totalNegatives = data.get('total negatives')

	correct = data.get('correct')
	incorrect = data.get('incorrect')

	truePositives = data.get('true positives')
	trueNegatives = data.get('true negatives')
	falsePositives = data.get('false positives')
	falseNegatives = data.get('false negatives')

	positivePrecision = float(truePositives) / (truePositives + falsePositives)
	positiveRecall = float(truePositives) / totalPositives
	negativePrecision = float(trueNegatives) / (trueNegatives + falseNegatives)
	negativeRecall = float(trueNegatives) / totalNegatives
	
	print '\n'
	print ' # OF FRAMES:                    ' + str(total)
	print ' # OF GOOD FRAMES:               ' + str(totalPositives)
	print ' # OF BAD FRAMES:                ' + str(totalNegatives)
	print ' -----'
	print ' # OF CORRECT IDENTIFICATIONS:   ' + str(correct)
	print ' # OF INCORRECT IDENTIFICATIONS: ' + str(incorrect)
	print ' -----'
	print ' # OF TRUE POSITIVES:            ' + str(truePositives)
	print ' # OF TRUE NEGATIVES:            ' + str(trueNegatives)
	print ' # OF FALSE POSITIVES:           ' + str(falsePositives)
	print ' # OF FALSE NEGATIVES:           ' + str(falseNegatives)
	print ' -----'
	print ' POSITIVE PRECISION:             ' + str(positivePrecision)
	print ' POSITIVE RECALL:                ' + str(positiveRecall)
	print ' NEGATIVE PRECISION:             ' + str(negativePrecision)
	print ' NEGATIVE RECALL:                ' + str(negativeRecall)
	print '\n'




def main(argv=None):

	#command = sys.argv[1]

	suggest = [0,0,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,0,1,1,0,0,0,0,1]
	answers = [1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0]
	comparison = simpleCompare(suggest, answers)

	print suggest
	print answers
	sectionCompare(suggest, answers)
	calcError(comparison)


	return


if __name__ == '__main__': 
	main()