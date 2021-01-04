import math
import numpy as np

class ModulatorConfig:
    def __init__(self, delay, waveformPeriodLength, waveformLength, sampleRate, randomNumberRange, waveformMod):
        self.delay = delay
        self.waveformPeriodLength = waveformPeriodLength
        self.waveformLength = waveformLength
        self.sampleRate = sampleRate
        self.randomNumberRange = randomNumberRange
        self.waveformMod = waveformMod

    def generateWaveform(self, randomNumbers):
        waveformPositions = [i * self.waveformPeriodLength for i in range(0, len(randomNumbers))]
        waveformPositionsInt = [math.floor(i) for i in waveformPositions + [self.waveformLength]]
        waveformLengthes = [waveformPositionsInt[i + 1] - waveformPositionsInt[i] for i in range(0, len(randomNumbers))]
        waveform = []
        waveformUnits = self.generateWaveformUnits()

        print(self.waveformLength)
        for i in range(0, len(randomNumbers)):
            rn = randomNumbers[i]
            length = waveformLengthes[i]
            waveform += waveformUnits[rn][:length]
            if len(waveform) >= self.waveformLength: break
        delaySample = -int(self.delay * (self.sampleRate / 1e9))
        waveform = waveform[delaySample:] + waveform[:delaySample]
        return waveform[:self.waveformLength]

    def generateWaveformUnits(self):
        waveforms = []
        for i in range(0, self.randomNumberRange):
            waveform = self._generateWaveformUnit(i)
            waveforms.append(waveform)
        return waveforms

    def _generateWaveformUnit(self, randomNumber):
        width, amp = self.waveformMod(randomNumber)
        pulseSample = math.ceil((width + 0.001) * 1e-9 * self.sampleRate)
        totalSample = math.ceil(self.waveformPeriodLength)
        leadingSample = math.ceil((self.waveformPeriodLength - pulseSample) / 2)
        a = [0] * leadingSample + [amp] * pulseSample + [0] * (totalSample - leadingSample - pulseSample)
        return a


class AWGEncoder:
    def __init__(self, asyncInvoker, channelMapping, randonNumberRange=128, phaseSlice=16):
        self.awg = asyncInvoker
        self.channelMapping = channelMapping
        self.randonNumberRange = randonNumberRange
        self.phaseSlice = phaseSlice
        self.config = {
            'sampleRate': 2e9,
            'randomNumbers': [i for i in range(randonNumberRange)],
            'waveformLength': randonNumberRange * 20,
            'ampReferenceSignal': 0.1,
            'ampReference': 0.9,
            'ampDecoyReference': 1,
            'ampDecoyZ': 0.9,
            'ampDecoyX': 0.5,
            'ampDecoyY': 0.2,
            'ampDecoyO': 0,
            'ampsPM1': [i / phaseSlice for i in range(phaseSlice)],
            'ampsPM2': [i / phaseSlice for i in range(phaseSlice)],
            'pulseWidthReferenceSignal': 2.6,
            'pulseWidthReference': 9.5,
            'pulseWidthDecoy': 2,
            'pulseWidthDecoyReference': 8,
            'pulseWidthPM1': 5,
            'pulseWidthPM2': 9.8,
            'delayReference': 100,
            'delayDecoy': 0,
            'delayPM1': 0,
            'delayPM2': 0,
        }

    def configure(self, key, value):
        if self.config.__contains__(key):
            self.config[key] = value
        else:
            raise RuntimeError('Bad configuration')

    def __modReference(self, randomNumber):
        rRef = (randomNumber & 0b1000000) >> 6
        return [self.config['pulseWidthReferenceSignal'], self.config['pulseWidthReference']][rRef], [self.config['ampReferenceSignal'], self.config['ampReference']][rRef]

    def __modDecoy(self, randomNumber):
        rRef = (randomNumber & 0b1000000) >> 6
        rDecoy = (randomNumber & 0b11)
        return [self.config['pulseWidthDecoy'], self.config['pulseWidthDecoyReference']][rRef], [[self.config['ampDecoyO'], self.config['ampDecoyX'], self.config['ampDecoyY'], self.config['ampDecoyZ']][rDecoy], self.config['ampDecoyReference']][rRef]

    def __modPM1(self, randomNumber):
        rPhase = (randomNumber & 0b111100) >> 2
        return self.config['pulseWidthPM1'], self.config['ampsPM1'][rPhase]

    def __modPM2(self, randomNumber):
        rPhase = (randomNumber & 0b111100) >> 2
        return self.config['pulseWidthPM2'], self.config['ampsPM2'][rPhase]

    def generateWaveforms(self):
        waveformPeriodLength = self.config['waveformLength'] / len(self.config['randomNumbers'])
        modulatorConfigs = {
            'AMRef': ModulatorConfig(self.config['delayReference'], waveformPeriodLength, self.config['waveformLength'], self.config['sampleRate'], self.randonNumberRange, self.__modReference),
            'AMDecoy': ModulatorConfig(self.config['delayDecoy'], waveformPeriodLength, self.config['waveformLength'], self.config['sampleRate'], self.randonNumberRange, self.__modDecoy),
            'PM1': ModulatorConfig(self.config['delayPM1'], waveformPeriodLength, self.config['waveformLength'], self.config['sampleRate'], self.randonNumberRange, self.__modPM1),
            'PM2': ModulatorConfig(self.config['delayPM2'], waveformPeriodLength, self.config['waveformLength'], self.config['sampleRate'], self.randonNumberRange, self.__modPM2),
        }
        waveforms = {}
        for waveformName in modulatorConfigs.keys():
            config = modulatorConfigs.get(waveformName)
            waveform = config.generateWaveform(self.config['randomNumbers'])
            waveforms[waveformName] = waveform
        return waveforms

    async def generateNewWaveform(self, returnWaveform=False):
        try:
            if self.awg:
                await self.awg.turnOffAllChannels()
            waveforms = self.generateWaveforms()
            for waveformName in waveforms:
                waveform = waveforms[waveformName]
                channelIndex = self.channelMapping[waveformName]
                if self.awg: await self.awg.writeWaveform(channelIndex, [(d - 0.5) * 2 * 32765 for d in waveform])
            if returnWaveform:
                return waveforms
        except BaseException as e:
            import logging
            logging.exception(e)

    async def startAllChannels(self):
        await self.awg.turnOnAllChannels()

    async def stopAllChannels(self):
        await self.awg.turnOffAllChannels()

    async def startChannel(self, name):
        await self.__setChannelStatus(name, True)

    async def stopChannel(self, name):
        await self.__setChannelStatus(name, False)

    async def __setChannelStatus(self, name, on):
        if self.channelMapping.__contains__(name):
            v = self.channelMapping[name]
            if on:
                await self.awg.turnOn(v)
            else:
                await self.awg.turnOff(v)
        else:
            raise RuntimeError('Channel {} not exists.'.format(name))

def showWaveform(waveforms, showRange=None):
    import matplotlib.pyplot as plt
    sampleCount = len(list(waveforms.values())[0])
    times = np.linspace(0, 0.5 * (sampleCount - 1), sampleCount)

    fig, axs = plt.subplots(4, 1)
    fig.set_size_inches(18, 10)

    for i in range(len(waveforms.keys())):
        axs[i].plot(times, waveforms[list(waveforms.keys())[i]])
        axs[i].grid()
    plt.show()


if __name__ == '__main__':
    from interactionfreepy import IFBroker, IFWorker, IFLoop
    import time
    import sys
    from tornado.ioloop import IOLoop
    from random import Random

    worker = IFWorker('tcp://192.168.25.5:224')
    dev = AWGEncoder(worker.asyncInvoker("USTCAWG_237"), {'AMRef': 1, 'AMDecoy': 2, 'PM1': 3, 'PM2': 4})
    worker.bindService("AWGEncoder", dev)
    IFLoop.join()


    # rnd = Random()
    # dev = AWGEncoder(None, {'AMRef': 1, 'AMDecoy': 2, 'PM1': 3, 'PM2': 4})
    # broker = IFBroker('tcp://*:2224')
    # worker = IFWorker('tcp://localhost:2224', 'AWGEncoder', dev)
    remoteDev = worker.AWGEncoder
    # remoteDev = dev

    remoteDev.configure('sampleRate', 2e9)
    remoteDev.configure('randomNumbers', [i for i in range(128)])
    remoteDev.configure('waveformLength', 128 * 20)
    remoteDev.configure('ampReferenceSignal', 0.1)
    remoteDev.configure('ampReference', 0.9)
    remoteDev.configure('ampDecoyReference', 1)
    remoteDev.configure('ampDecoyZ', 0.9)
    remoteDev.configure('ampDecoyX', 0.2)
    remoteDev.configure('ampDecoyY', 0.1)
    remoteDev.configure('ampDecoyO', 0)
    remoteDev.configure('ampsPM1', [i / 15 for i in range(16)])
    remoteDev.configure('ampsPM2', [(15 - i) / 15 for i in range(16)])
    remoteDev.configure('pulseWidthReferenceSignal', 2.6)
    remoteDev.configure('pulseWidthReference', 9.8)
    remoteDev.configure('pulseWidthDecoy', 3)
    remoteDev.configure('pulseWidthDecoyReference', 9.8)
    remoteDev.configure('pulseWidthPM1', 8)
    remoteDev.configure('pulseWidthPM2', 4)
    # remoteDev.configure('delayReference', 30)
    # remoteDev.configure('delayDecoy', 14)
    # remoteDev.configure('delayPM1', 500)
    # remoteDev.configure('delayPM2', -500)






    waveforms = remoteDev.generateNewWaveform(True)
    showWaveform(waveforms)
