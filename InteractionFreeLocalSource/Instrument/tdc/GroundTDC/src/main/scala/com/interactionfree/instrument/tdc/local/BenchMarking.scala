package com.interactionfree.instrument.tdc.local

import java.io.RandomAccessFile
import java.nio.file.{Files, Path, Paths}
import java.time.{LocalDateTime, ZoneOffset}

import com.interactionfree.{IFWorker, MsgpackSerializer}
import com.interactionfree.instrument.tdc.{DataBlock, GroundTDC, MultiHistogramAnalyser}
import com.interactionfree.instrument.tdc.application.MDIQKDQBERAnalyser

import scala.collection.mutable
import scala.collection.mutable.ListBuffer
import scala.jdk.CollectionConverters._

class BenchMarking(dataPath: String) {

  val dataBlock = loadDataBlockFile()
  val analyser = new MDIQKDQBERAnalyser(16)
  analyser.turnOn(Map("AliceRandomNumbers" -> Range(0, 10000).map(_ => 6).toList, "BobRandomNumbers" -> Range(0, 10000).map(_ => 6).toList, "Period" -> 4000.0, "Delay" -> 500.0, "PulseDiff" -> 2000.0,
    "Gate" -> 1000.0, "TriggerChannel" -> 0, "Channel 1" -> 8, "Channel 2" -> 9, "Channel Monitor Alice" -> 4, "Channel Monitor Bob" -> 5, "QBERSectionCount" -> 1000, "HOMSidePulses" -> List(-100, -90, -80, 80, 90, 100), "ChannelMonitorSyncChannel" -> 2,
    "BenchMarking" -> this))
  private val tags = ListBuffer[Tuple2[String, Long]]()

  def perform() = {
    Range(0, 10).foreach(_ => analyser.dataIncome(dataBlock))
    analyser.executionContext.shutdown()

    val tagDiffs = tags.drop(1).zip(tags.dropRight(1)).map(z => (z._2._1, z._1._1, (z._1._2 - z._2._2) / 1e6)).filter(z => z._1 != "Finish").map(z => (s"${z._1} -> ${z._2}", z._3))
    val tagSet = tagDiffs.map(_._1).toSeq.distinct
    val tagDiffAverage = tagSet.map(t => {
      val related = tagDiffs.filter(z => z._1 == t).map(_._2)
      (t, related.sum / related.size)
    })
    tagDiffAverage.foreach(z => println(f"${(z._1 + "                                             ").substring(0, 35)}: ${z._2}%.1f ms"))
  }

  def tag(tag: String) = tags addOne(tag, System.nanoTime())

  private def loadDataBlockFile() = {
    val raf = new RandomAccessFile(dataPath, "r")
    val bytes = new Array[Byte](raf.length().toInt)
    raf.readFully(bytes)
    raf.close()
    val dataBlockMap = MsgpackSerializer.deserialize(bytes).asInstanceOf[Map[String, Any]]
    val content = dataBlockMap("Content").asInstanceOf[List[List[Long]]].map(_.toArray).toArray
    val dataBlock = new DataBlock(content, dataBlockMap("CreationTime").asInstanceOf[Long], dataBlockMap("DataTimeBegin").asInstanceOf[Long], dataBlockMap("DataTimeEnd").asInstanceOf[Long])
    dataBlock
  }

  //  def dealDataBlock(dataBlockFile: Path) = {
  //
  //    // step 2: load parseOnline configuration
  //    val fetchTime = LocalDateTime.ofEpochSecond(dataBlockMap("CreationTime").asInstanceOf[Long] / 1000, ((dataBlockMap("CreationTime").asInstanceOf[Long] % 1000) * 1000000).toInt, ZoneOffset.ofHours(8))
  //    val worker = GroundTDC.worker
  //    val storage = worker.blockingInvoker("Storage")
  //    val fetchedOnlineData = storage.get(GroundTDC.properties.getProperty("Storage.Collection"), s"${fetchTime}+08:00", "FetchTime", filter = Map("FetchTime" -> 1, "Data" -> 1)).asInstanceOf[Map[String, Any]]
  //    val fetchedOnlineData_MDIQKDQBER = fetchedOnlineData("Data").asInstanceOf[Map[String, Any]]("MDIQKDQBER").asInstanceOf[Map[String, Any]]
  //    val fetchedOnlineData_MDIQKDQBER_configuration = collection.mutable.HashMap[String, Any](fetchedOnlineData_MDIQKDQBER("Configuration").asInstanceOf[Map[String, Any]].toSeq: _*)
  //
  //    // step 2.5 make some chanage
  //    fetchedOnlineData_MDIQKDQBER_configuration("AliceRandomNumbers") = Range(0, 10000).map(i => if (i % 2 == 0) 6 else 0).toList
  //    fetchedOnlineData_MDIQKDQBER_configuration("BobRandomNumbers") = Range(0, 10000).map(i => if (i % 2 == 0) 6 else 0).toList
  //    dataBlock.content(0) = dataBlock.content(0).zipWithIndex.filter(z => z._2 % 10 == 0).map(_._1)
  //
  //    // step 3: start a MDIQKD Analysiser
  //    val analyserMDIQKDQBER = new MDIQKDQBERAnalyser(16)
  //    analyserMDIQKDQBER.turnOn(fetchedOnlineData_MDIQKDQBER_configuration.toMap)
  //
  //    //    // step 3.5: plot a Histogram
  //    //    val analyserMultiHistogram = new MultiHistogramAnalyser(16)
  //    //    analyserMultiHistogram.turnOn(Map("Sync" -> "8", "Signals" -> List(9), "ViewStart" -> -200000, "ViewStop" -> 200000, "BinCount" -> 1000, "Divide" -> 1))
  //    //    analyserMultiHistogram.dataIncome(dataBlock) match {
  //    //      case None => throw new RuntimeException
  //    //      case Some(result) =>{
  //    //        //        println(result)
  //    //      }
  //    //    }
  //    //
  //    // setep 4: parse a DataBlock
  //    analyserMDIQKDQBER.dataIncome(dataBlock) match {
  //      case None => throw new RuntimeException
  //      case Some(result) => {
  //        val reProcessCollection = GroundTDC.properties.getProperty("Storage.Collection.ReProcess")
  //        storage.delete(reProcessCollection, s"${fetchTime}+08:00", "FetchTime")
  //        storage.append(reProcessCollection, Map("MDIQKDQBER" -> result), s"${fetchTime}+08:00")
  //      }
  //    }
  //
  //  }
}

object BenchMarking {
  def start() = {
    new BenchMarking("E:\\MDIQKD_Parse\\DataBlock\\2020-07-25T15-37-45.318.datablock").perform()
  }
}