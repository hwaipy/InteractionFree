# Control USTC AWGs
import math
import numpy as np

class ModulatorConfig:
    def __init__(self, duty, delay, diff, waveformPeriodLength, waveformLength, ampMod):
        self.duty = duty
        self.delay = delay
        self.diff = diff
        self.waveformPeriodLength = waveformPeriodLength
        self.waveformLength = waveformLength
        self.ampMod = ampMod

    def generateWaveform(self, randomNumbers, firstPulseMode):
        waveformPositions = [i * self.waveformPeriodLength for i in range(0, len(randomNumbers))]
        waveformPositionsInt = [math.floor(i) for i in waveformPositions + [self.waveformLength]]
        waveformLengthes = [waveformPositionsInt[i + 1] - waveformPositionsInt[i] for i in range(0, len(randomNumbers))]
        waveform = []
        waveformUnits = self.generateWaveformUnits()
        for i in range(0, len(randomNumbers)):
            rn = randomNumbers[i]
            length = waveformLengthes[i]
            if firstPulseMode and i > 0:
                waveform += [0] * length
            else:
                waveform += waveformUnits[rn][:length]
            if len(waveform) >= self.waveformLength: break
        delaySample = -int(self.delay * 2.5)
        waveform = waveform[delaySample:] + waveform[:delaySample]
        return waveform[:self.waveformLength]

    def generateWaveformUnits(self, ):
        waveforms = []
        for i in range(0, 8):
            waveform = self._generateWaveformUnit(i)
            waveforms.append(waveform)
        return waveforms

    def _generateWaveformUnit(self, randomNumber):
        waveform = []
        for i in range(0, math.ceil(self.waveformPeriodLength)):
            position = i * 1.0 / self.waveformPeriodLength
            if (position <= self.duty):
                pulseIndex = 0
            elif (position >= self.diff and position <= (self.diff + self.duty)):
                pulseIndex = 1
            else:
                pulseIndex = -1
            amp = self.ampMod(pulseIndex, randomNumber)
            waveform.append(amp)
        return waveform


class AWGEncoder:
    def __init__(self, worker, awgNames):
        self.worker = worker
        self.awgNames = awgNames
        self.awgs = [self.worker.asyncInvoker(name) for name in self.awgNames]
        self.sampleRate = 2e9
        self.waveformLength = 10 * 10 * 25
        self.randomNumbers = [0] * 10
        self.firstPulseMode = False
        self.specifiedRandomNumber = -1
        self.ampDecoyZ = 1
        self.ampDecoyX = 0.4
        self.ampDecoyY = 0.8
        self.ampDecoyO = 0
        self.ampTime = 1
        self.ampPM = 0.7
        self.ampPR = 0.7
        self.pulseWidthDecoy = 1.99
        self.pulseWidthTime0 = 1.9
        self.pulseWidthTime1 = 1.9
        self.pulseWidthPM = 2
        self.pulseWidthPR = 2
        self.pulseDiff = 3
        self.delayDecoy = 0
        self.delayTime1 = 0
        self.delayTime2 = 0
        self.delayPM = 0
        self.delayPR = 0
        self.channelMapping = {
            'AMDecoy': [0, 3],
            'AMTime1': [1, 1],
            'AMTime2': [1, 3],
            'PM': [0, 2],
        }

    def setRandomNumbers(self, rns):
        self.randomNumbers = rns

    def configure(self, key, value):
        if 'waveformLength'.__eq__(key):
            self.waveformLength = value
        elif 'delayDecoy'.__eq__(key):
            self.delayDecoy = value
        elif 'delayPM'.__eq__(key):
            self.delayPhase = value
        elif 'delayPR'.__eq__(key):
            self.delayPhaseRandomization = value
        elif 'delayTime0'.__eq__(key):
            self.delayTime1 = value
        elif 'delayTime1'.__eq__(key):
            self.delayTime2 = value
        elif 'pulseWidthDecoy'.__eq__(key):
            self.pulseWidthDecoy = value
        elif 'pulseWidthTime0'.__eq__(key):
            self.pulseWidthTime0 = value
        elif 'pulseWidthTime1'.__eq__(key):
            self.pulseWidthTime1 = value
        elif 'pulseWidthPM'.__eq__(key):
            self.pulseWidthPM = value
        elif 'pulseWidthPR'.__eq__(key):
            self.pulseWidthPR = value
        elif 'pulseDiff'.__eq__(key):
            self.pulseDiff = value
        elif 'ampDecoyZ'.__eq__(key):
            self.ampDecoyZ = value
        elif 'ampDecoyX'.__eq__(key):
            self.ampDecoyX = value
        elif 'ampDecoyY'.__eq__(key):
            self.ampDecoyY = value
        elif 'ampDecoyO'.__eq__(key):
            self.ampDecoyO = value
        elif 'ampTime'.__eq__(key):
            self.ampTime = value
        elif 'ampPM'.__eq__(key):
            self.ampPM = value
        elif 'ampPR'.__eq__(key):
            self.ampPR = value
        elif 'firstLaserPulseMode'.__eq__(key):
            self.firstPulseMode = value
        elif 'specifiedRandomNumber'.__eq__(key):
            self.specifiedRandomNumber = value
        else:
            raise RuntimeError('Bad configuration')

    def __ampModDecoy(self, pulseIndex, randomNumber):
        if pulseIndex >= 0:
            if randomNumber + pulseIndex != 7:
                return [self.ampDecoyO, self.ampDecoyX, self.ampDecoyY, self.ampDecoyZ][int(randomNumber / 2)]
        return 0

    def __ampModTime1(self, pulseIndex, randomNumber):  # decoy=0->vacuum->high level->pass
        if pulseIndex == -1: return 0
        decoy = int(randomNumber / 2)
        if decoy == 0:
            return 0
        elif decoy == 1 or decoy == 2:
            return 1
        else:
            return (pulseIndex == randomNumber % 2) * self.ampTime

    def __ampModTime2(self, pulseIndex, randomNumber):
        if pulseIndex == -1: return 0
        decoy = int(randomNumber / 2)
        if decoy == 0:
            return 1
        elif decoy == 1 or decoy == 2:
            return 0
        else:
            return (pulseIndex != randomNumber % 2) * self.ampTime

    def __ampModPhase(self, pulseIndex, randomNumber):
        if pulseIndex == -1:
            return 0.5
        else:
            # return ((pulseIndex == 0) and (randomNumber % 2 == 1)) * self.ampPM
            encode = randomNumber % 2
            return 0.5 + self.ampPM / 2 * math.pow(-1, pulseIndex + encode)

    # Defination of Random Number:
    # parameter ``randomNumbers'' should be a list of RN
    # RN is an integer.
    # RN/2 can be one of {0, 1, 2, 3}, stands for O, X, Y ,Z
    # RN%2 represent for encoding (0, 1)
    def generateWaveforms(self):
        waveformPeriodLength = self.waveformLength / len(self.randomNumbers)
        waveformPeriod = waveformPeriodLength * 1e9 / self.sampleRate
        modulatorConfigs = {
            'AMDecoy': ModulatorConfig(self.pulseWidthDecoy / waveformPeriod, self.delayDecoy,
                                       self.pulseDiff / waveformPeriod, waveformPeriodLength,
                                       self.waveformLength, self.__ampModDecoy),
            'AMTime1': ModulatorConfig(self.pulseWidthTime0 / waveformPeriod, self.delayTime1,
                                       self.pulseDiff / waveformPeriod, waveformPeriodLength,
                                       self.waveformLength, self.__ampModTime1),
            'AMTime2': ModulatorConfig(self.pulseWidthTime1 / waveformPeriod, self.delayTime2,
                                       self.pulseDiff / waveformPeriod, waveformPeriodLength,
                                       self.waveformLength, self.__ampModTime1),
            'PM': ModulatorConfig(self.pulseWidthPM / waveformPeriod, self.delayPM,
                                  self.pulseDiff / waveformPeriod, waveformPeriodLength, self.waveformLength,
                                  self.__ampModPhase),
            # 'PR': ModulatorConfig(self.pulseWidthPR / waveformPeriod, self.delayPR,
            #                       self.pulseDiff / waveformPeriod, waveformPeriodLength, self.waveformLength,
            #                       self.__ampModPR)
        }
        waveforms = {}
        for waveformName in modulatorConfigs.keys():
            config = modulatorConfigs.get(waveformName)
            waveform = config.generateWaveform(self.randomNumbers, self.firstPulseMode)
            waveforms[waveformName] = waveform
        return waveforms

    async def generateNewWaveform(self, returnWaveform=False):
        for awg in self.awgs:
            await awg.beginSession()
            await awg.turnOffAllChannels()
        waveforms = self.generateWaveforms()
        for waveformName in waveforms:
            waveform = waveforms[waveformName]
            channelIndex = self.channelMapping[waveformName]
            await self.awgs[channelIndex[0]].writeWaveform(channelIndex[1], [(2 * v - 1) * 32765 for v in waveform])
        for awg in self.awgs:
            await awg.endSession()
        if returnWaveform:
            return waveforms

    async def startPlay(self):
        for key in self.channelMapping:
            v = self.channelMapping[key]
            await self.awgs[v[0]].turnOn(v[1])
        await self.awgs[0].sendTrigger(200e-6, 100000)
        # self.dev._start()


if __name__ == '__main__':
    from IFWorker import IFWorker
    from IFCore import IFLoop

    worker = IFWorker('tcp://172.16.60.199:224')
    dev = AWGEncoder(worker, ['USTCAWG_Test_1A', 'USTCAWG_Test_1B'])
    worker.bindService('AWGEncoderTest', dev)
    try:
        # randomNumbersAlice = [0, 1, 2, 3, 4, 5, 6, 7]
        # dev.configure('firstLaserPulseMode', False)
        # dev.configure('waveformLength', len(randomNumbersAlice) * 8)
        # dev.configure('pulseWidthDecoy', 0.9)
        # dev.configure('pulseWidthTime0', 1.9)
        # dev.configure('pulseWidthTime1', 1.9)
        # dev.configure('pulseWidthPM', 1.9)
        # dev.configure('pulseWidthPR', 1.9)
        # dev.configure('pulseDiff', 1.9)
        # dev.configure('ampDecoyZ', 1)
        # dev.configure('ampDecoyX', 0.4)
        # dev.configure('ampDecoyY', 0.8)
        # dev.configure('ampDecoyO', 0)
        # dev.configure('ampTime', 1)
        # dev.configure('ampPM', 1)
        # # dev.configure('ampPR', 1)
        # dev.configure('delayDecoy', 0)
        # dev.configure('delayTime0', 0)
        # dev.configure('delayTime1', 0)
        # dev.configure('delayPM', 0)
        # dev.configure('delayPR', 0)
        # dev.setRandomNumbers(randomNumbersAlice)
        # dev.generateNewWaveform()
        # dev.startPlay()
        IFLoop.join()
    finally:
        worker.close()
