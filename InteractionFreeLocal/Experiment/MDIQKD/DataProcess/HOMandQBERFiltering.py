from IFWorker import IFWorker
from functional import seq
import numpy as np
from datetime import datetime
import time
from IFCore import debug_timerecord


class Reviewer:
    def __init__(self, worker, collectionTDC, collectionMonitor, collectionResult, startTime, stopTime):
        self.worker = worker
        self.collectionTDC = collectionTDC
        self.collectionMonitor = collectionMonitor
        self.collectionResult = collectionResult
        self.startTime = startTime
        self.stopTime = stopTime
        debug_timerecord('ready to review')

    def review(self):
        qberSections = seq(self.worker.Storage.range(self.collectionTDC, self.startTime, self.stopTime, by='FetchTime', filter={'FetchTime': 1, 'Data.MDIQKDQBER.ChannelMonitorSync': 1})).map(lambda m: QBERSection(m))
        qbersList = QBERs.create(qberSections)
        debug_timerecord('QBER List ready')
        channelSections = seq(self.worker.Storage.range(self.collectionMonitor, self.startTime, self.stopTime, by='FetchTime', filter={'Data.Triggers': 1, 'Data.TimeFirstSample': 1, 'Data.TimeLastSample': 1})).map(lambda m: ChannelSection(m))
        channelsList = Channels.create(channelSections)
        debug_timerecord('Channel List ready')

        dataPairs = qbersList.map(lambda qber: [qber, channelsList.filter(lambda channel: np.abs(qber.systemTime - channel.channelMonitorSyncs[0]) < 3)]).filter(lambda z: z[1].size() > 0).map(lambda z: [z[0], z[1][0]]).list()
        debug_timerecord('Data Pairs ready')
        for dataPair in dataPairs:
            debug_timerecord('in parse a data pair')
            dpp = DataPairParser(dataPair[0], dataPair[1],
                                 lambda id, filter: self.worker.Storage.get(self.collectionTDC, id, filter),
                                 lambda id, filter: self.worker.Storage.get(self.collectionMonitor, id, filter),
                                 lambda result, fetchTime: self.worker.Storage.append(self.collectionResult, result, fetchTime),
                                 [[0, -0.4, 4.5], [-1, 0, 5]])
            debug_timerecord('a data pair created')
            dpp.parse()
            debug_timerecord('a data pair parsed')
            dpp.release()
            debug_timerecord('a data pair released')
        debug_timerecord('All done')


class HOMandQBEREntry:
    def __init__(self, ratioLow, ratioHigh):
        self.ratioLow = ratioLow
        self.ratioHigh = ratioHigh
        self.homCounts = np.zeros((6))
        self.qberCounts = np.zeros((32))
        self.validSectionCount = 0

    def append(self, qberEntry):
        self.homCounts += qberEntry.HOMs
        self.qberCounts += qberEntry.QBERs
        self.validSectionCount += 1

    def toData(self):
        return [self.ratioLow, self.ratioHigh, self.validSectionCount] + [i for i in self.homCounts] + [i for i in self.qberCounts]


class DataPairParser:
    def __init__(self, qbers, channels, getterTDC, getterMonitor, resultUploader, channelMonitorConfig):
        self.qbers = qbers
        self.channels = channels
        self.resultUploader = resultUploader
        self.channelMonitorConfig = channelMonitorConfig
        self.qbers.load(getterTDC)
        self.channels.load(getterMonitor)
        self.__performTimeMatch()
        self.__performEntryMatch()
        self.timeMatchedQBEREntries = self.qbers.entries.filter(lambda e: e.relatedPowerCount > 0)

    def parse(self):
        debug_timerecord('in data pair parse', 1)
        result = {}
        result['CountChannelRelations'] = self.__countChannelRelations()
        result['HOMandQBERs'] = self.HOMandQBERs(1.02, 200)
        self.resultUploader(result, self.qbers.sections[0].meta['FetchTime'])
        debug_timerecord('done data pair parse', 1)

    def __performTimeMatch(self):
        qberSyncPair = self.qbers.channelMonitorSyncs
        timeUnit = (qberSyncPair[1] - qberSyncPair[0]) / (self.channels.riseIndices[1] - self.channels.riseIndices[0])
        firstRiseIndex = self.channels.riseIndices[0]
        seq(range(self.channels.riseIndices[0], self.channels.riseIndices[1])).for_each(lambda i: self.channels.entries[i].setTDCTime((i - firstRiseIndex) * timeUnit + qberSyncPair[0]))

    def __performEntryMatch(self):
        channelSearchIndexStart = 0
        channelEntrySize = self.channels.entries.size()
        for entry in self.qbers.entries.list():
            channelSearchIndex = channelSearchIndexStart
            while channelSearchIndex < channelEntrySize:
                channelEntry = self.channels.entries[channelSearchIndex]
                if channelEntry.tdcTime < entry.tdcStart:
                    channelSearchIndex += 1
                    channelSearchIndexStart += 1
                elif channelEntry.tdcTime < entry.tdcStop:
                    entry.appendRelatedChannelEntry(channelEntry)
                    channelSearchIndex += 1
                else:
                    break

    def __countChannelRelations(self):
        debug_timerecord('countChannelRelations', 10)
        data = self.timeMatchedQBEREntries.map(lambda e: e.counts + e.relatedPowers()).list()
        m = {'Heads': ['Count 1', 'Count 2', 'Power 1', 'Power 2'], 'Data': data}
        debug_timerecord('countChannelRelations', 10)
        return m

    def HOMandQBERs(self, ratioBase, ratioMaxIndex):
        ratios = list(np.logspace(-ratioMaxIndex, ratioMaxIndex, 2 * ratioMaxIndex + 1, base=ratioBase))
        debug_timerecord('HOMandQBERs', 10)
        ratioPairs = seq([0] + ratios).zip(ratios + [1e100])
        homAndQberEntries = ratioPairs.map(lambda ratioPair: HOMandQBEREntry(ratioPair[0], ratioPair[1]))

        def getRatioPairIndex(powers):
            p1 = 1 if self.channelMonitorConfig[0][0] < 0 else powers[self.channelMonitorConfig[0][0]] - self.channelMonitorConfig[0][1]
            p2 = 1 if self.channelMonitorConfig[1][0] < 0 else powers[self.channelMonitorConfig[1][0]] - self.channelMonitorConfig[1][1]
            if p1 == 0 or p2 > self.channelMonitorConfig[1][2]:
                index = 0
            elif p2 == 0 or p1 > self.channelMonitorConfig[0][2]:
                index = 2 * ratioMaxIndex + 1
            else:
                index = np.max([np.min([ratioMaxIndex + int(np.floor(np.log10(p1 / p2) / np.log10(1.02))) + 1, 2 * ratioMaxIndex + 1]), 0])
            return index

        self.timeMatchedQBEREntries.for_each(lambda entry: homAndQberEntries[getRatioPairIndex(entry.relatedPowers())].append(entry))
        totalEntryCount = self.timeMatchedQBEREntries.size()
        r = homAndQberEntries.map(lambda e: e.toData()).list()
        debug_timerecord('HOMandQBERs', 10)
        return {'TotalEntryCount': totalEntryCount, 'SortedEntries': r}

    def release(self):
        self.qbers.release()
        self.channels.release()


class QBERs:
    def __init__(self, sections):
        self.sections = seq(sections)
        self.systemTime = sections[0].pcTime
        self.TDCTimeOfSectionStart = sections[0].tdcStart
        self.channelMonitorSyncs = seq([self.sections[0], self.sections[-1]]).map(lambda s: (s.slowSync - self.TDCTimeOfSectionStart) / 1e12)
        #     val valid = math.abs(channelMonitorSyncs(1) - channelMonitorSyncs(0) - 10) < 0.001

    def load(self, getter):
        self.sections.for_each(lambda z: z.load(getter))
        debug_timerecord('{} qber section loaded'.format(self.sections.size()))

        def createQBEREntryList(section):
            entryCount = len(section.contentCountEntries)

            def createQBEREntry(i):
                entryTDCStartStop = seq([i, i + 1]).map(lambda j: ((section.tdcStop - section.tdcStart) / entryCount * j + section.tdcStart - self.TDCTimeOfSectionStart) / 1e12)
                entryHOMs = section.contentHOMEntries[i]
                entryQBERs = section.contentQBEREntries[i]
                entryCounts = section.contentCountEntries[i]
                return QBEREntry(entryTDCStartStop[0], entryTDCStartStop[1], entryHOMs, entryCounts, entryQBERs)

            return seq(range(entryCount)).map(lambda i: createQBEREntry(i))

        self.entries = self.sections.map(lambda section: createQBEREntryList(section)).flatten()
        debug_timerecord('entries loaded', 1)

    def release(self):
        self.sections.for_each(lambda z: z.release())

    @classmethod
    def create(cls, entries):
        syncedEntryIndices = seq(entries).zip_with_index().filter(lambda z: z[0].slowSync).map(lambda z: z[1])
        return syncedEntryIndices[:-1].zip(syncedEntryIndices[1:]).map(lambda z: QBERs(entries[z[0]:z[1] + 1]))


class QBERSection:
    def __init__(self, meta):
        self.meta = meta
        self.dbID = meta['_id']
        self.data = meta["Data"]
        self.mdiqkdQberMeta = self.data['MDIQKDQBER']
        syncs = self.mdiqkdQberMeta['ChannelMonitorSync']
        self.tdcStart = syncs[0]
        self.tdcStop = syncs[1]
        self.slowSync = None if len(syncs) <= 2 else syncs[2]
        self.pcTime = datetime.fromisoformat(self.meta['FetchTime']).timestamp()

    def load(self, getter):
        self.content = getter(self.dbID, {'Data.DataBlockCreationTime': 1, 'Data.MDIQKDQBER': 1})
        self.contentData = self.content['Data']
        self.contentQBER = self.contentData['MDIQKDQBER']
        self.contentQBEREntries = self.contentQBER['QBER Sections']
        self.contentHOMEntries = self.contentQBER['HOM Sections']
        self.contentCountEntries = self.contentQBER['Count Sections']

    def release(self):
        self.content = None
        self.contentData = None
        self.contentQBER = None
        self.contentQBEREntries = None
        self.contentHOMEntries = None
        self.contentCountEntries = None


class QBEREntry:
    def __init__(self, tdcStart, tdcStop, HOMs, counts, QBERs):
        self.tdcStart = tdcStart
        self.tdcStop = tdcStop
        self.HOMs = HOMs
        self.counts = counts
        self.QBERs = QBERs
        self.relatedPowerCount = 0
        self.power1Sum = 0
        self.power2Sum = 0

    def appendRelatedChannelEntry(self, entry):
        self.power1Sum += entry.power1
        self.power2Sum += entry.power2
        self.relatedPowerCount += 1

    def relatedPowers(self):
        if self.relatedPowerCount == 0: return [0.0, 0.0]
        return [self.power1Sum / self.relatedPowerCount, self.power2Sum / self.relatedPowerCount]


class Channels:
    def __init__(self, sections):
        self.sections = seq(sections)
        self.channelMonitorSyncs = seq([sections[0], sections[-1]]).map(lambda s: s.trigger / 1000)
        self.valid = np.abs(self.channelMonitorSyncs[1] - self.channelMonitorSyncs[0] - 10) < 0.1

    def load(self, getter):
        self.sections.for_each(lambda z: z.load(getter))
        debug_timerecord('{} channel section loaded'.format(self.sections.size()))

        def createChannelEntryList(section):
            channel1 = section.contentChannel1
            channel2 = section.contentChannel2
            pcTimeUnit = (section.timeLastSample - section.timeFirstSample) / (len(channel1) - 1)
            return seq(range(0, len(channel1))).map(lambda i: ChannelEntry(channel1[i], channel2[i], section.timeFirstSample + i * pcTimeUnit))

        self.entries = self.sections.map(lambda section: createChannelEntryList(section)).flatten().cache()
        self.riseIndices = [self.sections.first().riseIndex(), self.sections.last().riseIndex() + self.sections.init().map(lambda s: len(s.contentChannel1)).sum()]
        debug_timerecord('entries loaded')

    def release(self):
        seq(self.sections).for_each(lambda z: z.release())

    @classmethod
    def create(cls, entries):
        syncedEntryIndices = seq(entries).zip_with_index().filter(lambda z: z[0].trigger).map(lambda z: z[1])
        return syncedEntryIndices[:-1].zip(syncedEntryIndices[1:]).map(lambda z: Channels(entries[z[0]:z[1] + 1]))


class ChannelSection:
    def __init__(self, meta):
        self.meta = meta
        self.data = meta['Data']
        self.dbID = meta['_id']
        triggers = self.data['Triggers']
        self.trigger = None if len(triggers) == 0 else triggers[0]
        timeFirstSample_ms = self.data['TimeFirstSample']
        timeLastSample_ms = self.data['TimeLastSample']
        self.timeFirstSample = timeFirstSample_ms / 1e3
        self.timeLastSample = timeLastSample_ms / 1e3

    def load(self, getter):
        self.content = getter(self.dbID, {'Data.Channel1': 1, 'Data.Channel2': 1})
        self.contentData = self.content['Data']
        self.contentChannel1 = self.contentData['Channel1']
        self.contentChannel2 = self.contentData['Channel2']

    def release(self):
        self.content = None
        self.contentData = None
        self.contentChannel1 = None
        self.contentChannel2 = None

    def riseIndex(self):
        pcTimeUnit = (self.timeLastSample - self.timeFirstSample) / (len(self.contentChannel1) - 1)
        riseIndex = int(np.ceil((self.trigger / 1e3 - self.timeFirstSample) / pcTimeUnit))
        return riseIndex


class ChannelEntry:
    def __init__(self, power1, power2, pcTime):
        self.power1 = power1
        self.power2 = power2
        self.pcTime = pcTime
        self.tdcTime = -1

    def setTDCTime(self, tdcTime):
        self.tdcTime = tdcTime


if __name__ == '__main__':
    mainWorker = IFWorker("tcp://127.0.0.1:224", "TDCLocalParserTest")
    # mainWorker = IFWorker("tcp://172.16.60.199:224", "TDCLocalParserTest")
    try:
        t1 = time.time()
        # reviewer = Reviewer(mainWorker, 'TDCLocalTest_10k100M', 'MDIChannelMonitor', 'MDI_DataReviewer_10k100M', '2020-04-30T23:34+08:00', '2020-05-01T00:59+08:00')
        reviewer = Reviewer(mainWorker, 'TDCLocalTest_10k250M', 'MDIChannelMonitor', 'MDI_DataReviewer_10k250M', '2020-05-01T01:12:32+08:00', '2020-05-01T02:59+08:00') # start from 30th QBER section
        reviewer.review()
        t2 = time.time()
        print('Finished in {} s.'.format(t2 - t1))
    finally:
        mainWorker.close()
