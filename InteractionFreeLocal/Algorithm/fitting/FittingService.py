class FittingService:
    def __init__(self):
        pass

    def singlePeakGaussianFit(self, xs, ys):
        return GaussianFit.singlePeakGaussianFit(xs, ys)

    def riseTimeFit(self, xs, ys):
        try:
            return RiseTimeFit.riseTimeFit(xs, ys)
        except Exception as e:
            import traceback
            msg = traceback.format_exc()  # 方式1
            print(msg)
            return 0.0

    def sinFit(self, xs, ys, paraW=None):
        return SinFit.sinFit(xs, ys, paraW)


if __name__ == '__main__':
    from IFWorker import IFWorker
    from IFCore import IFLoop

    endpoint = 'tcp://127.0.0.1:224'
    serviceName = 'FittingService'

    worker = IFWorker(endpoint, serviceName, FittingService())
    IFLoop.join()
