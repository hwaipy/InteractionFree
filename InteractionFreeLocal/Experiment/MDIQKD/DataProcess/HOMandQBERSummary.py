import os
from datetime import datetime
import math
import matplotlib.pyplot as plt
import sys
import numpy as np
from IFWorker import IFWorker
from datetime import datetime
import time
import numpy as np


class Shower:
    def __init__(self, worker, collection, begin, end):
        self.worker = worker
        self.collection = collection
        self.begin = begin
        self.end = end

    def show(self):
        ids = self.worker.Storage.range(self.collection, self.begin, self.end, by='FetchTime', filter={})
        if len(ids) == 0:
            print('No Record.')
            return
        conditions = None
        mergedData = None
        for id in ids[:]:
            content = self.worker.Storage.get(self.collection, id['_id'], {'Data': 1})['Data']
            countChannelRelations = content['CountChannelRelations']
            countChannelRelationsData = np.array(countChannelRelations['Data'])
            # plt.scatter(countChannelRelationsData[:, 0], countChannelRelationsData[:, 2])
            # plt.scatter(countChannelRelationsData[:, 1], countChannelRelationsData[:, 3])
            # plt.show()
            # plt.close()
            HOMandQBERs = content['HOMandQBERs']
            totalEntryCount = HOMandQBERs['TotalEntryCount']
            data = np.array(HOMandQBERs['SortedEntries'])
            condition = data[:, :2]
            tobeMerged = data[:, 2:]
            if conditions is None:
                conditions = condition
                mergedData = tobeMerged
            else:
                mergedData += tobeMerged

        data = np.hstack((conditions, mergedData))

        # plot non filtering
        threshold = 0.8
        ratios = np.logspace(-1.3, 1.3, 100)
        thresholdedData = []
        for ratio in ratios:
            ratioLow = ratio * threshold
            ratioHigh = ratio / threshold
            mask = np.vstack((conditions[:, 1] > ratioLow, conditions[:, 0] < ratioHigh)).all(0)
            selectedData = data[mask]
            summedData = np.sum(selectedData, 0)[2:]
            thresholdedData.append(summedData)
        thresholdedData = np.array(thresholdedData)
        thresholdedData = np.hstack((ratios.reshape(100, 1), thresholdedData))
        self.__plot(threshold, thresholdedData)

    #         selectedRatio = self.__min(np.array([d for d in data if d[0] == max(thresholds)]), head, 'HOM',
    #                                    'AllDip', 'AllAct')[0]
    #         selectedData = np.array([row for row in data if row[1] == selectedRatio])
    #         for bases in ['XX', 'YY', 'All']:
    #             self.__plot(selectedData, head, selectedRatio, 'Ratio', 'Threshold', 'HOM', '{}Dip'.format(bases),
    #                         '{}Act'.format(bases), bases, True, False)
    #         for bases in ['XX', 'YY', 'ZZ']:
    #             self.__plot(selectedData, head, selectedRatio, 'Ratio', 'Threshold', 'QBER', '{} Correct'.format(bases),
    #                         '{} Wrong'.format(bases), bases, True, False)

    def __plot(self, threshold, data):
        ratios = data[:, 0]
        validTimes = data[:, 1]
        HOMs = data[:, 2: 8]
        QBERs = data[:, 8:]
        fig, axs = plt.subplots(2, 3, figsize=(20, 10))
        for i in range(3):
            ax = axs[0, i]
            ax2 = ax.twinx()
            ax.semilogx(ratios, HOMs[:, i * 2] / (HOMs[:, i * 2 + 1] - 1e-10), color='blue')
            ax2.semilogx(ratios, HOMs[:, i * 2 + 1], color='orange')
            ax.set_ylim((0.4, 2))
            ax.grid()
        plt.show()
        # independents = data[:, head.index(independentName)]


#         c1 = data[:, head.index(head1)]
#         c2 = data[:, head.index(head2)]
#         saveFileName = '{}-{}={}-{}.png'.format(mode, eigenValueName, eigenValue, bases)
#         if mode == 'HOM':
#             y2 = c2
#             y1 = c1 / (c2 + 1e-10)
#             y1Label = 'HOM Dip ({})'.format(bases)
#             y2Label = 'Side Coincidences'
#         elif mode == 'QBER':
#             y2 = c1 + c2
#             y1 = c2 / (y2 + 1e-10)
#             y1Label = 'QBER ({})'.format(bases)
#             y2Label = 'Coincidences'
#         else:
#             raise RuntimeError('Mode not valid.')
#
#         fig = plt.figure()
#         ax1 = fig.add_subplot(111)
#         if log:
#             ax1.semilogx(independents, y1, label=y1Label)
#         else:
#             ax1.plot(independents, y1, label=y1Label)
#         ax1.set_ylabel(y1Label)
#         ax1.set_xlabel(independentName)
#         ax1.grid(True, which="both", color="k", ls="--", lw=0.3)
#         ax2 = ax1.twinx()
#         if log:
#             ax2.semilogx(independents, y2, 'green', label=y2Label)
#         else:
#             ax2.plot(independents, y2, 'green', label=y2Label)
#         ax2.set_ylabel(y2Label)
#         plt.legend()
#         if save:
#             plt.savefig('{}/{}'.format(self.showDir, saveFileName), dpi=300)
#         else:
#             plt.show()
#         plt.close()
#
#     def __min(self, data, head, mode, head1, head2):
#         ratios = data[:, 1]
#         c1 = data[:, head.index(head1)]
#         c2 = data[:, head.index(head2)]
#         if mode == 'HOM':
#             y = c1 / (c2 + 1e-10)
#         elif mode == 'QBER':
#             y = c2 / (c1 + c2 + 1e-10)
#         else:
#             raise RuntimeError('Mode not valid.')
#         z = [z for z in zip(y, ratios)]
#         z.sort()
#         validZ = [zz for zz in z if zz[1] > 0.1 and zz[1] < 10][0]
#         return (validZ[1], validZ[0])
#
#     def __listValidResults(self):
#         files = [f for f in os.listdir(self.dir) if f.lower().endswith('.png')]
#         files.sort()
#         dirs = ['{}/{}'.format(self.dir, file[:15]) for file in files]
#         return dirs


if __name__ == '__main__':
    print('HOM and QBER summary')
    # worker = IFWorker('tcp://172.16.60.199:224')
    worker = IFWorker('tcp://127.0.0.1:224')
    # shower = Shower(worker, 'MDI_DataReviewer_10k100M', '2020-03-12 11:04:05', '2020-06-12 22:04:05')
    shower = Shower(worker, 'MDI_DataReviewer_10k250M', '2020-03-12 11:04:05', '2020-06-12 22:04:05')
    shower.show()
    worker.close()