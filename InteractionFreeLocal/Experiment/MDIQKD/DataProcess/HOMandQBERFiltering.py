from IFWorker import IFWorker
from functional import seq
import numpy as np
from datetime import datetime


class Reviewer:
    def __init__(self, worker, collectionTDC, collectionMonitor, collectionResult, startTime, stopTime):
        self.worker = worker
        self.collectionTDC = collectionTDC
        self.collectionMonitor = collectionMonitor
        self.collectionResult = collectionResult
        self.startTime = startTime
        self.stopTime = stopTime

    def review(self):
        qberSections = seq(self.worker.Storage.range(self.collectionTDC, self.startTime, self.stopTime, by='FetchTime', filter={'FetchTime': 1, 'Data.MDIQKDQBER.ChannelMonitorSync': 1})).map(lambda m: QBERSection(m))
        qbersList = QBERs.create(qberSections)
        channelSections = seq(self.worker.Storage.range(self.collectionMonitor, self.startTime, self.stopTime, by='FetchTime', filter={'Data.Triggers': 1, 'Data.TimeFirstSample': 1, 'Data.TimeLastSample': 1})).map(lambda m: ChannelSection(m))
        channelsList = Channels.create(channelSections)

        dataPairs = qbersList.map(lambda qber: [qber, channelsList.filter(lambda channel: np.abs(qber.systemTime - channel.channelMonitorSyncs[0]) < 3)]).filter(lambda z: z[1].size() > 0).map(lambda z: [z[0], z[1][0]])
        for dataPair in dataPairs[:1]:
            dpp = DataPairParser(dataPair[0], dataPair[1],
                                 lambda id, filter: self.worker.Storage.get(self.collectionTDC, id, filter),
                                 lambda id, filter: self.worker.Storage.get(self.collectionMonitor, id, filter),
                                 lambda result, fetchTime: self.worker.Storage.append(self.collectionResult, result, fetchTime))
            dpp.parse()
            dpp.release()
            print("parsed")


#
#   object HOMandQBEREntry {
#     private val bases = List("O", "X", "Y", "Z")
#     val HEAD = s"Threshold, Ratio, ValidTime, " +
#       (List("XX", "YY", "All").map(bb => List("Dip", "Act").map(position => bb + position)).flatten.mkString(", ")) + ", " +
#       (bases.map(a => bases.map(b => List("Correct", "Wrong").map(cw => a + b + " " + cw))).flatten.flatten.mkString(", "))
#   }
#
#   class HOMandQBEREntry(val ratioLow: Double, val ratioHigh: Double, val powerOffsets: Tuple2[Double, Double] = (0, 0), val powerInvalidLimit: Double = 4.5) {
#     private val homCounts = new Array[Double](6)
#     private val qberCounts = new Array[Int](32)
#     private val validSectionCount = new AtomicInteger(0)
#
#     def ratioAcceptable(rawPower1: Double, rawPower2: Double) = {
#       val power1 = rawPower1 - (if (ignoredChannel == 0) powerOffsets._1 else 0)
#       val power2 = rawPower2 - (if (ignoredChannel == 1) powerOffsets._2 else 0)
#       val actualRatio = if (power2 == 0) 0 else power1 / power2
#       if (power1 > powerInvalidLimit || power2 > powerInvalidLimit) false
#       else (actualRatio >= ratioLow) && (actualRatio < ratioHigh)
#     }
#
#     def append(qberEntry: QBEREntry) = {
#       val homs = qberEntry.HOMs
#       Range(0, 3).foreach(kk => {
#         homCounts(kk * 2) += homs(kk * 2)
#         homCounts(kk * 2 + 1) += homs(kk * 2 + 1)
#       })
#       val qbers = qberEntry.QBERs
#       Range(0, qberCounts.size).foreach(kk => qberCounts(kk) += qbers(kk))
#       validSectionCount.incrementAndGet
#     }
#
#     def toData(): Array[Double] = Array[Double](ratioLow, ratioHigh, validSectionCount.get) ++ homCounts ++ qberCounts.map(_.toDouble)
#   }
class DataPairParser:
    def __init__(self, qbers, channels, getterTDC, getterMonitor, resultUploader):
        self.qbers = qbers
        self.channels = channels
        self.qbers.load(getterTDC)
        self.channels.load(getterMonitor)
        self.resultUploader = resultUploader
        self.__performTimeMatch()
        self.__performEntryMatch()

    # //    val timeMatchedQBEREntries = if (hasExternalPowerMonitor) qbers.entries.filter(e => e.relatedPowerCount > 0) else qbers.entries
    #     //    val powerOffsets = (timeMatchedQBEREntries.map(p => p.relatedPowers._1).min, timeMatchedQBEREntries.map(p => p.relatedPowers._2).min)
    #
    def parse(self):
        result = {}
        result['CountChannelRelations'] = self.__countChannelRelations()

        #     //      val halfRatio = Range(0, 200).map(i => math.pow(1.02, i))
        #     //      val ratios = halfRatio.reverse.dropRight(1).map(a => 1 / a) ++ halfRatio
        #     //      result("HOMandQBERs") = HOMandQBERs(ratios.toList)
        print(self.qbers.sections[0].meta['FetchTime'])

        self.resultUploader(result, self.qbers.sections[0].meta['FetchTime'])

    def __performTimeMatch(self):
        qberSyncPair = self.qbers.channelMonitorSyncs
        timeUnit = (qberSyncPair[1] - qberSyncPair[0]) / (self.channels.riseIndices[1] - self.channels.riseIndices[0])
        firstRiseIndex = self.channels.riseIndices[0]
        seq(range(self.channels.riseIndices[0], self.channels.riseIndices[1])).for_each(lambda i: self.channels.entries[i].setTDCTime((i - firstRiseIndex) * timeUnit + qberSyncPair[0]))

    def __performEntryMatch(self):
        channelSearchIndexStart = 0
        channelEntrySize = self.channels.entries.size()
        for QBEREntry in self.qbers.entries:
            channelSearchIndex = channelSearchIndexStart
            while channelSearchIndex < channelEntrySize:
                channelEntry = self.channels.entries[channelSearchIndex]
                if channelEntry.tdcTime < QBEREntry.tdcStart:
                    channelSearchIndex += 1
                    channelSearchIndexStart += 1
                elif channelEntry.tdcTime < QBEREntry.tdcStop:
                    QBEREntry.appendRelatedChannelEntry(channelEntry)
                    channelSearchIndex += 1
                else:
                    break

    def __countChannelRelations(self):
        pass
        return 'CCR'

    #     //      val counts = timeMatchedQBEREntries.map(_.counts)
    #     //      val powers = timeMatchedQBEREntries.map(_.relatedPowers)
    #     //      Map("Counts 1" -> counts.map(_ (0)), "Counts 2" -> counts.map(_ (1)), "Powers 1" -> powers.map(_._1), "Powers 2" -> powers.map(_._2))
    #     //    }
    #     //
    #     //    private def HOMandQBERs(ratios: List[Double]) = {
    #     //      val ratioPairs = (List(0) ++ ratios).zip(ratios ++ List(Double.MaxValue))
    #     //      val homAndQberEntries = ratioPairs.map(ratioPair => new HOMandQBEREntry(ratioPair._1, ratioPair._2, powerOffsets)).toArray
    #     //      timeMatchedQBEREntries.foreach(entry => {
    #     //        val relatedPowers = entry.relatedPowers
    #     //        homAndQberEntries.filter(_.ratioAcceptable(relatedPowers._1, relatedPowers._2)).foreach(hqe => hqe.append(entry))
    #     //      })
    #     //      val totalEntryCount = timeMatchedQBEREntries.size
    #     //      val r = homAndQberEntries.map(e => e.toData()).toList
    #     //      Map("TotalEntryCount" -> totalEntryCount, "SortedEntries" -> r)
    #     //    }
    #   }
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
    #

    def load(self, getter):
        self.sections.for_each(lambda z: z.load(getter))

        def createQBEREntryList(section):
            entryCount = len(section.contentCountEntries)

            def createQBEREntry(i):
                entryTDCStartStop = seq([i, i + 1]).map(lambda j: ((section.tdcStop - section.tdcStart) / entryCount * j + section.tdcStart - self.TDCTimeOfSectionStart) / 1e12)
                entryHOMs = seq(section.contentHOMEntries).map(lambda j: j[i])
                entryQBERs = section.contentQBEREntries[i]
                entryCounts = section.contentCountEntries[i]
                return QBEREntry(entryTDCStartStop[0], entryTDCStartStop[1], entryHOMs, entryCounts, entryQBERs)

            return seq(range(entryCount)).map(lambda i: createQBEREntry(i))

        self.entries = self.sections.map(lambda section: createQBEREntryList(section)).flatten()

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
        self.relatedChannelEntries = []

    def appendRelatedChannelEntry(self, entry):
        self.relatedChannelEntries.append(entry)


#     private val relatedPower1 = new ArrayBuffer[Double]()
#     private val relatedPower2 = new ArrayBuffer[Double]()
#
#     def appendPowers(power1: Double, power2: Double) = {
#       relatedPower1 += power1
#       relatedPower2 += power2
#     }
#
#     def relatedPowerCount = relatedPower1.size
#
#     def relatedPowers =
#       if (relatedPowerCount == 0) (0.0, 0.0)
#       else (relatedPower1.sum / relatedPowerCount, relatedPower2.sum / relatedPowerCount)
#   }
#
class Channels:
    def __init__(self, sections):
        self.sections = seq(sections)
        self.channelMonitorSyncs = seq([sections[0], sections[-1]]).map(lambda s: s.trigger / 1000)
        self.valid = np.abs(self.channelMonitorSyncs[1] - self.channelMonitorSyncs[0] - 10) < 0.1

    def load(self, getter):
        self.sections.for_each(lambda z: z.load(getter))

        def createChannelEntryList(section):
            channel1 = section.contentChannel1
            channel2 = section.contentChannel2
            pcTimeUnit = (section.timeLastSample - section.timeFirstSample) / (len(channel1) - 1)
            return seq(range(0, len(channel1))).map(lambda i: ChannelEntry(channel1[i], channel2[i], section.timeFirstSample + i * pcTimeUnit))

        self.entries = self.sections.map(lambda section: createChannelEntryList(section)).flatten().cache()
        self.riseIndices = [self.sections.first().riseIndex(), self.sections.last().riseIndex() + self.sections.init().map(lambda s: len(s.contentChannel1)).sum()]

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
    try:
        reviewer = Reviewer(mainWorker, 'TDCLocalTest_10k100M', 'MDIChannelMonitor', 'MDI_DataReviewer_10k100M', '2020-04-30T23:34+08:00', '2020-05-01T00:59+08:00')
        reviewer.review()
    finally:
        mainWorker.close()
