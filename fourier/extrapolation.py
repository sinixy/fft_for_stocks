import numpy as np


def fourier_extrapolation(x, n_predict):
	n = x.size
	t = np.arange(0, n)
	p = np.polyfit(t, x, 1)
	x_notrend = x - p[0] * t
	x_freqdom = np.fft.fft(x_notrend)
	f = np.fft.fftfreq(n)

	indexes = list(range(n))
	indexes.sort(key=lambda i: abs(x_freqdom[i]))
	indexes.reverse()
	strongest_signals_cnt = int(len(indexes) * 0.15)
 
	t = np.arange(0, n + n_predict)
	restored_sig = np.zeros(t.size)
	for k in indexes[:strongest_signals_cnt]:
		ampli = np.absolute(x_freqdom[k]) / n
		phase = np.angle(x_freqdom[k])
		restored_sig += ampli * np.cos(2 * np.pi * f[k] * t + phase)
	Y = restored_sig + p[0] * t
	return Y