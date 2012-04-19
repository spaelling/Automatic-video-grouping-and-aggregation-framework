import math

def computeFrameStateAnders(magnitudes, contrast, p=0.015):
	
	states = []
	state_values = []
	
	T1 = 1.0 # contrast treshold
	T2 = 0.015 # displacement vector treshold
	# T2 = p
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

def computeFrameStateAnders2(magnitudes, contrast):
	
	states = []
	state_values = []
	
	T1 = .25 # contrast treshold
	T2 = .18 # displacement vector treshold
	T = (T1+T2)/2.0 # cumulative treshold

	# weights
	a = T / T1
	b = T / T2

	# print 'a: %2.2f, b: %2.2f' % (a,b)

	for i in range(0,len(magnitudes)):
		state_value = sum([a * contrast[i]**3, b * magnitudes[i]**3])**(1.0/3)
		state_values.append(state_value)		
	states = [v <= T for v in state_values]

	return states, state_values

def computeFrameStateSquare(magnitudes, contrast):
	
	states = []
	state_values = []
	
	T = 0.4

	for i in range(0,len(magnitudes)):
		state_value = math.sqrt(contrast[i]**2 + magnitudes[i]**2)
		state_values.append(state_value)		
	states = [v <= T for v in state_values]

	return states, state_values	

def computeFrameStateCubic(magnitudes, contrast):
	
	states = []
	state_values = []
	
	T = 0.4

	for i in range(0,len(magnitudes)):
		state_value = (contrast[i]**3 + magnitudes[i]**3)**(1.0/3.0)
		state_values.append(state_value)		
	states = [v <= T for v in state_values]

	return states, state_values	

# def computeFrameStateX(magnitudes, contrast, x=2.0, T=1.0):
	
# 	states = []
# 	state_values = []

# 	for i in range(0,len(magnitudes)):
# 		state_value = (contrast[i]**x + magnitudes[i]**x)**(1.0/x)
# 		state_values.append(state_value)		
# 	states = [v <= T for v in state_values]

# 	return states, state_values


def computeFrameStateLauge(magnitudes, contrast):
	
	states = []
	state_values = []
	
	contrast_lim = 0.75
	magnitudes_lim = 0.01

	for i in range(0,len(magnitudes)):
		state_value = max([contrast[i] * (1 / contrast_lim), magnitudes[i] * (1 / magnitudes_lim)])
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)


	return states, state_values


def computeFrameStateNaiive(magnitudes, contrast):
	
	states = []
	state_values = []
	
	for i in range(0,len(magnitudes)):
		states.append(1)
		state_values.append((contrast[i] + magnitudes[i])/2)

	return states, state_values


def computeFrameStateMagnitudeOnly(magnitudes):
	
	states = []
	state_values = []

	magnitudes_lim = 0.45
	
	for i in range(0,len(magnitudes)):
		state_value = magnitudes[i] * (1 / magnitudes_lim)
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)
		
	return states, state_values


def computeFrameStateContrastOnly(contrast):
	
	states = []
	state_values = []

	contrast_lim = 0.72
	
	for i in range(0,len(contrast)):
		state_value = contrast[i] * (1 / contrast_lim)
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)
		
	return states, state_values