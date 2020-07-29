package com.interactionfree.instrument.tdc.local

import java.io.RandomAccessFile
import java.net.Socket
import java.nio.file.{Files, Path, Paths}
import java.time.{LocalDateTime, ZoneOffset}
import java.util.concurrent.atomic.AtomicLong

import com.interactionfree.{IFWorker, MsgpackSerializer}
import com.interactionfree.instrument.tdc.{DataBlock, GroundTDC, MultiHistogramAnalyser}
import com.interactionfree.instrument.tdc.application.MDIQKDQBERAnalyser

import scala.collection.mutable
import scala.jdk.CollectionConverters._

object LocalTDCDataFeeder {
  private val localDataRoot = "E:\\MDIQKD_Parse\\ReviewForCode\\20200501012120-012720-10k250M-decoy"
  //  private val localDataRoot = "/Users/hwaipy/Downloads/TDCParse/20200501DavidAliceHOMTDC数据-排查筛选问题/20200501011320-011820-10k250M-all"
  private val localDataFiles = Files.list(Paths.get(localDataRoot)).iterator().asScala.toList.sorted
  private val startTime = localDataFiles.head.getFileName.toString.split("-").head.toLong
  private val dataBlockCount = new AtomicLong(0)

  def start(port: Int, dataRate: Int = 20000000) = {
    Thread.sleep(2000)
    val worker = IFWorker(GroundTDC.IFServerAddress)
    val process = worker.blockingInvoker(GroundTDC.IFServerServiceName)
    process.turnOnAnalyser("Counter")
    //    process.turnOnAnalyser("Histogram", Map("Sync" -> 0, "Signal" -> 8, "ViewStart" -> 0, "ViewStop" -> 10000000, "Divide" -> 1000))
    process.turnOnAnalyser("MultiHistogram", Map("Sync" -> 0, "Signals" -> List(4, 5, 8, 9), "ViewStart" -> 0, "ViewStop" -> 4000000, "Divide" -> 1000, "BinCount" -> 200))
    process.turnOnAnalyser("CoincidenceHistogram", Map("ChannelA" -> 8, "ChannelB" -> 9, "ViewStart" -> -200000, "ViewStop" -> 200000, "BinCount" -> 1000))
    process.turnOnAnalyser("MDIQKDEncoding", Map("Period" -> 4000.0, "TriggerChannel" -> 0, "SignalChannel" -> 8, "TimeAliceChannel" -> 4, "TimeBobChannel" -> 5, "BinCount" -> 100, "RandomNumbers" -> Range(0, 10000).map(_ => 6).toList))
    process.turnOnAnalyser("MDIQKDQBER", Map("AliceRandomNumbers" -> Range(0, 10000).map(_ => 6).toList, "BobRandomNumbers" -> Range(0, 10000).map(_ => 6).toList, "Period" -> 4000.0, "Delay" -> 500.0, "PulseDiff" -> 2000.0,
      "Gate" -> 1000.0, "TriggerChannel" -> 0, "Channel 1" -> 8, "Channel 2" -> 9, "Channel Monitor Alice" -> 4, "Channel Monitor Bob" -> 5, "QBERSectionCount" -> 1000, "HOMSidePulses" -> List(-100, -90, -80, 80, 90, 100), "ChannelMonitorSyncChannel" -> 2))

    //    process.setDelay(0, 11970700)
    process.setDelay(0, 10022000)
    //    process.setDelay(4, 22800)
    process.setDelay(4, 16800)
    //    process.setDelay(5, 44000)
    process.setDelay(5, 42000)
    process.setDelay(8, 0)
    process.setDelay(9, -510600)

    process.setPostProcessStatus(true)

    val socket = new Socket("localhost", port)
    val outputStream = socket.getOutputStream
    val buffer = new Array[Byte](1000000)
    localDataFiles.foreach(localDataFile => {
      val startTime = System.currentTimeMillis()
      val in = Files.newInputStream(localDataFile)
      val size = Files.size(localDataFile)
      val read = new AtomicLong(0)
      while (read.get < size) {
        val r = in.read(buffer)
        read.set(read.get + r)
        outputStream.write(buffer, 0, r)
        outputStream.flush()
        val expectedTime = (read.get / dataRate.toDouble * 1000).toLong + startTime
        val timeToWait = expectedTime - System.currentTimeMillis()
        if (timeToWait > 0) Thread.sleep(timeToWait)
      }
    })
    Thread.sleep(2000)
    socket.close()
    worker.close()
  }

  def getNextLocalDataBlockCreationTime = startTime + dataBlockCount.getAndIncrement() * 1000

}

object LocalDataBlockFeeder {
  def start() = {
    val dataBlockPath = GroundTDC.properties.getProperty("Storage.Local.DataBlock")
    val dataBlockFiles = Files.list(Paths.get(dataBlockPath)).iterator().asScala.toList.filter(p => p.toString.toLowerCase.endsWith(".datablock"))
    dataBlockFiles.foreach(dealDataBlock)
  }

  def dealDataBlock(dataBlockFile: Path) = {
    // step 1: load DataBlock
    val raf = new RandomAccessFile(dataBlockFile.toString, "r")
    val bytes = new Array[Byte](raf.length().toInt)
    raf.readFully(bytes)
    raf.close()
    val dataBlockMap = MsgpackSerializer.deserialize(bytes).asInstanceOf[Map[String, Any]]
    val content = dataBlockMap("Content").asInstanceOf[List[List[Long]]].map(_.toArray).toArray
    val dataBlock = new DataBlock(content, dataBlockMap("CreationTime").asInstanceOf[Long], dataBlockMap("DataTimeBegin").asInstanceOf[Long], dataBlockMap("DataTimeEnd").asInstanceOf[Long])

    // step 2: load parseOnline configuration
    val fetchTime = LocalDateTime.ofEpochSecond(dataBlockMap("CreationTime").asInstanceOf[Long] / 1000, ((dataBlockMap("CreationTime").asInstanceOf[Long] % 1000) * 1000000).toInt, ZoneOffset.ofHours(8))
    val worker = GroundTDC.worker
    val storage = worker.blockingInvoker("Storage")
    val fetchedOnlineData = storage.get(GroundTDC.properties.getProperty("Storage.Collection"), s"${fetchTime}+08:00", "FetchTime", filter = Map("FetchTime" -> 1, "Data" -> 1)).asInstanceOf[Map[String, Any]]
    val fetchedOnlineData_MDIQKDQBER = fetchedOnlineData("Data").asInstanceOf[Map[String, Any]]("MDIQKDQBER").asInstanceOf[Map[String, Any]]
    val fetchedOnlineData_MDIQKDQBER_configuration = collection.mutable.HashMap[String, Any](fetchedOnlineData_MDIQKDQBER("Configuration").asInstanceOf[Map[String, Any]].toSeq: _*)

    // step 2.5 make some chanage
    fetchedOnlineData_MDIQKDQBER_configuration("AliceRandomNumbers") = Range(0, 10000).map(i => if (i % 2 == 0) 6 else 0).toList
    fetchedOnlineData_MDIQKDQBER_configuration("BobRandomNumbers") = Range(0, 10000).map(i => if (i % 2 == 0) 6 else 0).toList
    dataBlock.content(0) = dataBlock.content(0).zipWithIndex.filter(z => z._2 % 10 == 0).map(_._1)

    // step 3: start a MDIQKD Analysiser
    val analyserMDIQKDQBER = new MDIQKDQBERAnalyser(16)
    analyserMDIQKDQBER.turnOn(fetchedOnlineData_MDIQKDQBER_configuration.toMap)

    //    // step 3.5: plot a Histogram
    //    val analyserMultiHistogram = new MultiHistogramAnalyser(16)
    //    analyserMultiHistogram.turnOn(Map("Sync" -> "8", "Signals" -> List(9), "ViewStart" -> -200000, "ViewStop" -> 200000, "BinCount" -> 1000, "Divide" -> 1))
    //    analyserMultiHistogram.dataIncome(dataBlock) match {
    //      case None => throw new RuntimeException
    //      case Some(result) =>{
    //        //        println(result)
    //      }
    //    }
    //
    // setep 4: parse a DataBlock
    analyserMDIQKDQBER.dataIncome(dataBlock) match {
      case None => throw new RuntimeException
      case Some(result) => {
        val reProcessCollection = GroundTDC.properties.getProperty("Storage.Collection.ReProcess")
        storage.delete(reProcessCollection, s"${fetchTime}+08:00", "FetchTime")
        storage.append(reProcessCollection, Map("MDIQKDQBER" -> result), s"${fetchTime}+08:00")
      }
    }

  }
}