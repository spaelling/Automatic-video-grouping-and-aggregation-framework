def computeFrameStateAnders(magnitudes, contrast):
	
	states = []
	state_values = []
	
	T1 = 0.80 # contrast treshold
	T2 = 1.85 # displacement vector treshold
	T = (T1+T2)/2.0 # cumulative treshold

	# weights
	a = T / T1
	b = T / T2

	# print 'a: %2.2f, b: %2.2f' % (a,b)

	for i in range(0,len(magnitudes)):
		state_value = sum([a * contrast[i], b * magnitudes[i]])	
		state_values.append(state_value)		
	states = [v <= T for v in state_values]

	return states, state_values


def computeFrameStateLauge(magnitudes, contrast):
	
	states = []
	state_values = []
	
	contrast_lim = 0.74
	magnitudes_lim = 0.45

	for i in range(0,len(magnitudes)):
		state_value = max([contrast[i] * (1 / contrast_lim), magnitudes[i] * (1 / magnitudes_lim)])
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)


	return states, state_values