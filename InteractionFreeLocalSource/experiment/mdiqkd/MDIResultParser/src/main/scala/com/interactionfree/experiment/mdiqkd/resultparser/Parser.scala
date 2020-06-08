package com.interactionfree.experiment.mdiqkd.resultparser

import java.time.LocalDateTime
import java.util.concurrent.atomic.{AtomicBoolean, AtomicInteger, AtomicReference}

import com.interactionfree.{BlockingIFWorker, IFWorker}
import com.interactionfree.NumberTypeConversions._

import scala.collection.mutable
import scala.collection.mutable.ArrayBuffer
import scala.language.postfixOps
//import java.io.PrintWriter
//import java.nio.file.{Files, Path, Paths, StandardCopyOption}
//import java.text.SimpleDateFormat
//import java.time.Duration
//import java.util.Date
//import java.util.concurrent.Executors
//import java.util.concurrent.atomic.{AtomicBoolean, AtomicInteger, AtomicReference}
//import com.hydra.core.MessageGenerator
//import scala.collection.mutable.{ArrayBuffer, ListBuffer}
//import scala.concurrent.{Await, ExecutionContext, Future}
//import scala.concurrent.duration._
//import scala.collection.JavaConverters._

class Reviewer(worker: BlockingIFWorker, startTime: LocalDateTime, stopTime: LocalDateTime, ignoredChannel: Int = -1) {
  private val qberSections = worker.Storage.range("TDCLocal", startTime.toString, stopTime.toString,
    Map("Data.DataBlockCreationTime" -> 1, "Data.MDIQKDQBER.ChannelMonitorSync" -> 1)
  ).asInstanceOf[List[Map[String, Any]]].map(meta => new QBERSection(meta))
  private val qbersList = QBERs(qberSections)

  private val channelSections = worker.Storage.range("MDIChannelMonitor", LocalDateTime.of(2020, 5, 5, 22, 22).toString, LocalDateTime.now().toString,
    Map("Data.triggers" -> 1, "Data.timeFirstSample" -> 1, "Data.timeLastSample" -> 1)).asInstanceOf[List[Map[String, Any]]].map(meta => new ChannelSection(meta))
  private val channelsList = Channels(channelSections)

  val dataPairs = qbersList.map(qber => (qber, channelsList.filter(channel => Math.abs(qber.systemTime - channel.channelMonitorSyncs.head) < 3).headOption)).filter(_._2.isDefined).map(z => (z._1, z._2.get))
  dataPairs.headOption.foreach(dataPair => {
    val dpp = new DataPairParser(dataPair._1, dataPair._2)
    dpp.parse()
  })


  object HOMandQBEREntry {
    private val bases = List("O", "X", "Y", "Z")
    val HEAD = s"Threshold, Ratio, ValidTime, " +
      (List("XX", "YY", "All").map(bb => List("Dip", "Act").map(position => bb + position)).flatten.mkString(", ")) + ", " +
      (bases.map(a => bases.map(b => List("Correct", "Wrong").map(cw => a + b + " " + cw))).flatten.flatten.mkString(", "))
  }

  class HOMandQBEREntry(val threshold: Double, val ratio: Double, val powerOffsets: Tuple2[Double, Double] = (0, 0), val powerInvalidLimit: Double = 4.5) {
    private val homCounts = new Array[Double](6)
    private val qberCounts = new Array[Int](32)
    private val validSectionCount = new AtomicInteger(0)

    def ratioAcceptable(rawPower1: Double, rawPower2: Double) = {
      val power1 = rawPower1 - (if (ignoredChannel == 0) powerOffsets._1 else 0)
      val power2 = rawPower2 - (if (ignoredChannel == 1) powerOffsets._2 else 0)
      val actualRatio = if (power2 == 0) 0 else power1 / power2 * ratio
      if (power1 > powerInvalidLimit || power2 > powerInvalidLimit) false
      else (actualRatio > threshold) && (actualRatio < (1 / threshold))
    }

    def append(qberEntry: QBEREntry) = {
      val homs = qberEntry.HOMs
      Range(0, 3).foreach(kk => {
        homCounts(kk * 2) += homs(kk * 2)
        homCounts(kk * 2 + 1) += homs(kk * 2 + 1)
      })
      val qbers = qberEntry.QBERs
      Range(0, qberCounts.size).foreach(kk => qberCounts(kk) += qbers(kk))
      validSectionCount.incrementAndGet
    }

    def toData(): Array[Double] = Array[Double](threshold, ratio, validSectionCount.get) ++ homCounts ++ qberCounts.map(_.toDouble)
  }

  class DataPairParser(val qbers: QBERs, val channels: Channels) {
    performTimeMatch
    performEntryMatch
    val timeMatchedQBEREntries = qbers.entries.filter(e => e.relatedChannelEntryCount > 0)
    val powerOffsets = (timeMatchedQBEREntries.map(p => p.relatedPowers._1).min, timeMatchedQBEREntries.map(p => p.relatedPowers._2).min)

    def parse() = {
      val result = new mutable.HashMap[String, Any]()
      result("CountChannelRelations") = countChannelRelations()
      val halfRatios = Range(0, 40).map(i => math.pow(1.1, i))
      val ratios = halfRatios.reverse.dropRight(1).map(a => 1 / a) ++ halfRatios
      result("HOMandQBERs") = HOMandQBERs(List(1e-10) ++ Range(1, 100).toList.map(i => i / 100.0), ratios.toList)
      //      worker.Storage.append("MDIQKD_DataReviewer", result)
    }

    private def performTimeMatch = {
      val qberSyncPair = qbers.channelMonitorSyncs
      val timeUnit = (qberSyncPair(1) - qberSyncPair(0)) / (channels.riseIndices(1) - channels.riseIndices(0))
      Range(channels.riseIndices(0), channels.riseIndices(1)).foreach(i => channels.entries(i).tdcTime set (i - channels.riseIndices(0)).toDouble * timeUnit + qberSyncPair(0))
    }

    private def performEntryMatch = {
      val channelSearchIndexStart = new AtomicInteger(0)
      qbers.entries.foreach(qberEntry => {
        val channelSearchIndex = new AtomicInteger(channelSearchIndexStart get)
        val break = new AtomicBoolean(false)
        while (channelSearchIndex.get() < channels.entries.size && !break.get) {
          val channelEntry = channels.entries(channelSearchIndex.get)
          if (channelEntry.tdcTime.get < qberEntry.tdcStart) {
            channelSearchIndex.incrementAndGet
            channelSearchIndexStart.incrementAndGet
          } else if (channelEntry.tdcTime.get < qberEntry.tdcStop) {
            qberEntry.appendRelatedChannelEntry(channelEntry)
            channelSearchIndex.incrementAndGet
          } else break set true
        }
      })
    }

    private def countChannelRelations(): Map[String, Any] = {
      val counts = timeMatchedQBEREntries.map(_.counts)
      val powers = timeMatchedQBEREntries.map(_.relatedPowers)
      Map("Counts 1" -> counts.map(_ (0)), "Counts 2" -> counts.map(_ (1)), "Powers 1" -> powers.map(_._1), "Powers 2" -> powers.map(_._2))
    }

    private def HOMandQBERs(thresholds: List[Double], ratios: List[Double]) = {
      val homAndQberEntries = thresholds.map(threshold => ratios.map(ratio => new HOMandQBEREntry(threshold, ratio, powerOffsets))).flatten.toArray
      timeMatchedQBEREntries.foreach(entry => {
        val relatedPowers = entry.relatedPowers
        homAndQberEntries.filter(_.ratioAcceptable(relatedPowers._1, relatedPowers._2)).foreach(hqe => hqe.append(entry))
      })
      val totalEntryCount = timeMatchedQBEREntries.size
      //      homAndQberEntries.map(e => e.)
    }
  }

  object QBERs {
    def apply(entries: List[QBERSection]) = {
      val syncedEntryIndices = entries.zipWithIndex.filter(z => z._1.slowSync.isDefined).map(_._2)
      syncedEntryIndices.dropRight(1).zip(syncedEntryIndices.drop(1)).map(iz => new QBERs(entries.slice(iz._1, iz._2 + 1)))
    }
  }

  class QBERs(val sections: List[QBERSection]) {
    val systemTime = sections.head.pcTime / 1e3
    val TDCTimeOfSectionStart = sections(0).tdcStart
    val channelMonitorSyncs = List(sections.head, sections.last).map(s => (s.slowSync.get - TDCTimeOfSectionStart) / 1e12)
    val valid = math.abs(channelMonitorSyncs(1) - channelMonitorSyncs(0) - 10) < 0.001

    lazy val entries = sections.map(section => {
      val entryCount = section.contentCountEntries.size
      Range(0, entryCount).map(i => {
        val entryTDCStartStop = List(i, i + 1).map(j => ((section.tdcStop - section.tdcStart) / entryCount * j + section.tdcStart - TDCTimeOfSectionStart) / 1e12)
        val entryHOMs = section.contentHOMEntries.map(j => j(i))
        val entryQBERs = section.contentQBEREntries(i)
        val entryCounts = section.contentCountEntries(i)
        new QBEREntry(entryTDCStartStop(0), entryTDCStartStop(1), entryHOMs, entryCounts, entryQBERs)
      })
    }).flatten.toArray
  }

  class QBERSection(meta: Map[String, Any]) {
    private val data = meta("Data").asInstanceOf[Map[String, Any]]
    private val mdiqkdQberMeta = data("MDIQKDQBER").asInstanceOf[Map[String, Any]]
    private val syncs = mdiqkdQberMeta("ChannelMonitorSync").asInstanceOf[IterableOnce[Any]].iterator.toArray
    private val dbID = meta("_id").toString
    val tdcStart: Long = syncs(0)
    val tdcStop: Long = syncs(1)
    val slowSync: Option[Long] = if (syncs.size > 2) Some(syncs(2)) else None
    val pcTime: Long = data("DataBlockCreationTime")

    lazy private val content = worker.Storage.get("TDCLocal", dbID, Map("Data.DataBlockCreationTime" -> 1, "Data.MDIQKDQBER" -> 1)).asInstanceOf[Map[String, Any]]
    lazy private val contentData = content("Data").asInstanceOf[Map[String, Any]]
    lazy private val contentQBER = contentData("MDIQKDQBER").asInstanceOf[Map[String, Any]]
    lazy val contentQBEREntries = contentQBER("QBER Sections").asInstanceOf[List[List[Int]]].map(_.toArray).toArray
    lazy val contentHOMEntries = contentQBER("HOM Sections").asInstanceOf[List[List[Double]]].map(_.toArray).toArray
    lazy val contentCountEntries = contentQBER("Count Sections").asInstanceOf[List[List[Int]]].map(_.toArray).toArray
  }

  class QBEREntry(val tdcStart: Double, val tdcStop: Double, val HOMs: Array[Double], val counts: Array[Int], val QBERs: Array[Int]) {
    private val relatedChannelEntryBuffer = new ArrayBuffer[ChannelEntry]()

    def appendRelatedChannelEntry(channelEntry: ChannelEntry) = relatedChannelEntryBuffer += channelEntry

    def relatedChannelEntryCount = relatedChannelEntryBuffer.size

    def relatedPowers =
      if (relatedChannelEntryCount == 0) (0.0, 0.0)
      else (relatedChannelEntryBuffer.map(e => e.power1).sum / relatedChannelEntryCount,
        relatedChannelEntryBuffer.map(e => e.power2).sum / relatedChannelEntryCount)
  }

  object Channels {
    def apply(entries: List[ChannelSection]) = {
      val syncedEntryIndices = entries.zipWithIndex.filter(z => z._1.trigger.isDefined).map(_._2)
      syncedEntryIndices.dropRight(1).zip(syncedEntryIndices.drop(1)).map(iz => new Channels(entries.slice(iz._1, iz._2 + 1)))
    }
  }

  class Channels(val sections: List[ChannelSection]) {
    val channelMonitorSyncs = List(sections.head, sections.last).map(s => s.trigger.get / 1000)
    val valid = math.abs(channelMonitorSyncs(1) - channelMonitorSyncs(0) - 10) < 0.1
    //  val systemTimes = sections.map(section => section("SystemTime"))
    lazy val entries = sections.map(section => {
      val channel1 = section.contentChannel1
      val channel2 = section.contentChannel2
      val pcTimeUnit = (section.timeLastSample - section.timeFirstSample) / (channel1.size - 1)
      Range(0, channel1.size).map(i => new ChannelEntry(channel1(i), channel2(i), section.timeFirstSample + i * pcTimeUnit))
    }).flatten.toArray
    lazy val riseIndices = channelMonitorSyncs.map(s => entries.indexWhere(_.pcTime > s))
  }

  class ChannelSection(meta: Map[String, Any]) {
    private val data = meta("Data").asInstanceOf[Map[String, Any]]
    private val triggers = data("triggers").asInstanceOf[List[Any]].map(i => {
      val d: Double = i
      d
    })
    val dbID = meta("_id").toString
    val trigger = triggers.headOption
    private val timeFirstSample_ms: Double = data("timeFirstSample")
    private val timeLastSample_ms: Double = data("timeLastSample")
    val timeFirstSample = timeFirstSample_ms / 1e3
    val timeLastSample = timeLastSample_ms / 1e3

    lazy private val content = worker.Storage.get("MDIChannelMonitor", dbID, Map("Data.channel1" -> 1, "Data.channel2" -> 1)).asInstanceOf[Map[String, Any]]
    lazy private val contentData = content("Data").asInstanceOf[Map[String, Any]]
    lazy val contentChannel1 = contentData("channel1").asInstanceOf[List[Double]].toArray
    lazy val contentChannel2 = contentData("channel2").asInstanceOf[List[Double]].toArray
  }

  class ChannelEntry(val power1: Double, val power2: Double, val pcTime: Double) {
    val tdcTime = new AtomicReference[Double](-1)
  }

}

object Parser extends App {
  val worker = IFWorker("tcp://127.0.0.1:224", "TDCLocalParserTest")
  Thread.sleep(1000)
  try {
    val reviewer = new Reviewer(worker, LocalDateTime.of(2020, 5, 10, 15, 0), LocalDateTime.of(2020, 5, 10, 16, 0))
  }
  catch {
    case e: Throwable => e.printStackTrace()
  } finally {
    worker.close()
  }
}