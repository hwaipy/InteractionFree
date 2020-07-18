import sys
from scipy.optimize import curve_fit
# from scipy import asarray as ar, exp
import numpy as np
import matplotlib.pyplot as plt

def riseTimeFit(xs, ys):
    # in case there is a large background
    bgs = ys[int(len(ys) * 0.8):-1]
    bg = sum(bgs) / len(bgs)
    ys = [y - bg for y in ys]

    SPD = [ys[0]]
    for y in ys[1:]:
        SPD.append(SPD[-1] + y)
    roughRise = 0
    for i in range(0, len(xs)):
        if SPD[i] > 0.04 * SPD[-1]:
            roughRise = xs[i]
            break

    fitXs = []
    fitYs = []
    for i in range(0, len(xs)):
        if xs[i] >= roughRise and xs[i] <= roughRise + 1.7:
            fitXs.append(xs[i])
            fitYs.append(SPD[i])

    def linear(x, a, b):
        return a * x + b

    expectA = (fitYs[0] - fitYs[-1]) / (fitXs[0] - fitXs[-1])
    expectB = fitYs[0] - expectA * fitXs[0]
    popt, pcov = curve_fit(linear, fitXs, fitYs, p0=[expectA, expectB])

    rise = -popt[1] / popt[0]
    return rise
