from IFWorker import IFWorker
from IFCore import IFLoop


class TDCLocalReviewer:
    def __init__(self):
        pass

    def dataIncome(self, data):
        print(data)


if __name__ == '__main__':
    worker = IFWorker('tcp://localhost:224', 'TDCLocalReviewer', TDCLocalReviewer())
    IFLoop.join()
