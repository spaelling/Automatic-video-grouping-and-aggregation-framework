def computeFrameStateAnders(magnitudes, contrast):
	
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
	states = [v <= T for v in state_values]

	return states, state_values


def computeFrameStateLauge(magnitudes, contrast):
	
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
		state_values.append(state_value)


	return states, state_values