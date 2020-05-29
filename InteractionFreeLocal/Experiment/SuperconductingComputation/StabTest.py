if __name__ == '__main__':
    from IFWorker import IFWorker
    from IFCore import IFLoop
    import time

    worker = IFWorker('tcp://172.16.60.199:224')

    dmm = worker.EO_DMM
    dc = worker.EO_DC
    dmm.setDCCurrentMeasurement(2e-3, autoRange=False, aperture=0.1)


    def readPower():
        return dmm.directMeasure(count=1)[0]


    def setVoltage(v):
        if v < 0: v = 0
        if v > 7: v = 7
        dc.setVoltage(0, v)


    target = 0.3e-3
    voltage = dc.getVoltageSetpoints()[0]
    step = -0.001
    while True:
        power = readPower()
        if power > target:
            voltage += step
        else:
            voltage -= step
        setVoltage(voltage)
        print(power, voltage)
        time.sleep(0.2)