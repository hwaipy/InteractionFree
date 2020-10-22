__author__ = 'Hwaipy'

from Instrument.Instruments import Instrument
from socketserver import BaseRequestHandler, TCPServer


class HMC7044Eval(Instrument):

    def __init__(self):
        self.channelCount = 14
        self.devices = {}
        self.digitalDelays = [0] * self.channelCount
        self.analogDelays = [0] * self.channelCount
        self.slipUnit = 0.40
        self.digitalDelayUnit = self.slipUnit / 2
        self.digitalDelayMax = 16
        self.analogDelayUnit = 0.025
        self.analogDelayMax = 2374
        self.residual = 0

    def setDelay(self, channel, delay):
        self.checkChannel(channel)
        # delay += self.
        currentTunableDelay = self.digitalDelays[channel] * self.digitalDelayUnit + self.analogDelays[channel] * self.analogDelayUnit
        realDelay = delay + currentTunableDelay
        slip = int(realDelay / self.slipUnit)
        residualDelay = realDelay - self.slipUnit * slip
        digitalDelay = int(residualDelay / self.digitalDelayUnit)
        analogDelay = int((residualDelay - (self.digitalDelayUnit * digitalDelay)) / self.analogDelayUnit)
        self.residual = residualDelay - self.digitalDelayUnit * digitalDelay + self.analogDelayUnit * analogDelay
        while (slip > 0):
            self.slip(channel, min(3000, slip))
            slip -= min(3000, slip)
        self.digitalDelay(channel, digitalDelay)
        self.analogDelay(channel, analogDelay)
        self.digitalDelays[channel] = digitalDelay
        self.analogDelays[channel] = analogDelay
        return residualDelay - self.digitalDelayUnit * digitalDelay + self.analogDelayUnit * analogDelay

    def setDivider(self, channel, divide):
        self.checkChannel(channel)
        self.checkRange(divide, 2, 4094)
        # if divide % 2 is not 0:
        #     raise RuntimeError('Only even are supported for divider.')
        self.setReg(0xC9 + channel * 10, divide)

    # slip $value$ clock circles. e.g. 0.333ns * value
    def slip(self, channel, value):
        self.checkChannel(channel)
        self.checkRange(value, 0, 4000)
        self.setReg(0xCD + channel * 10, value)
        time.sleep(0.1)
        self.setReg(2, 2)
        time.sleep(0.1)
        self.setReg(2, 0)
        # self.setReg(0xCD + channel * 10, 0)

    # 1/2 clock circle * delay. e.g. 0.167 ns. delay in [0, 16]
    def digitalDelay(self, channel, delay):
        self.checkChannel(channel)
        self.checkRange(delay, 0, self.digitalDelayMax)
        self.setReg(0xCC + channel * 10, delay)

    # 0.025 ns. delay in [0, 23]
    def analogDelay(self, channel, delay):
        self.checkChannel(channel)
        self.checkRange(delay, 0, self.analogDelayMax)
        self.setReg(0xCB + channel * 10, delay)

    def checkChannel(self, channel):
        self.checkRange(channel, 0, self.channelCount - 1, 'channel')

    def checkRange(self, value, min, max, valueName='value'):
        if value < min or value > max:
            raise RuntimeError('{} {} out of range: [{}, {}]'.format(valueName, value, min, max))

    def setReg(self, reg, value):
        if isinstance(reg, int) and isinstance(value, int) and reg >= 0 and value >= 0:
            msg = '{},{}'.format(reg, value)
            print(msg)
            for request in self.devices.keys():
                request.send('{}\n'.format(msg).encode('UTF-8'))

    def deviceConnected(self):
        return len(self.devices.keys()) > 0

    def newDevice(self, request):
        self.devices[request] = request

    def deleteDevice(self, request):
        del self.devices[request]


if __name__ == '__main__':
    import time
    from interactionfreepy import IFWorker

    dev = HMC7044Eval()
    worker = IFWorker('tcp://172.16.60.200:224', 'HMC7044EvalTest', dev)

    class EchoHandler(BaseRequestHandler):
        def handle(self):
            print('Got connection from', self.client_address)
            dev.newDevice(self.request)
            try:
                while True:
                    msg = self.request.recv(8192)
            finally:
                dev.deleteDevice(self.request)


    serv = TCPServer(('', 25001), EchoHandler)
    serv.serve_forever()
