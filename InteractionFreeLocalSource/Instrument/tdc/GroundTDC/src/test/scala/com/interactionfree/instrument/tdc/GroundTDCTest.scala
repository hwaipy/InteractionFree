package com.interactionfree.instrument.tdc

import java.io.RandomAccessFile
import java.time.{LocalDateTime, ZoneOffset}

import com.interactionfree.instrument.tdc.application.MDIQKDQBERAnalyser
import com.interactionfree.{IFWorker, Invocation, MsgpackSerializer}
import org.scalatest.BeforeAndAfter
import org.scalatest.funsuite.AnyFunSuite

import scala.language.postfixOps

class GroundTDCTest extends AnyFunSuite with BeforeAndAfter {
  //  test("Test MDIQKD.") {
  //    // step 1: load DataBlock
  //    val path = "E:\\MDIQKD_Parse\\DataBlock\\2020-07-25T15-37-45.318.datablock"
  //    val raf = new RandomAccessFile(path, "r")
  //    val bytes = new Array[Byte](raf.length().toInt)
  //    raf.readFully(bytes)
  //    val dataBlockMap = MsgpackSerializer.deserialize(bytes).asInstanceOf[Map[String, Any]]
  //    val content = dataBlockMap("Content").asInstanceOf[List[List[Long]]].map(_.toArray).toArray
  //    val dataBlock = new DataBlock(content, dataBlockMap("CreationTime").asInstanceOf[Long], dataBlockMap("DataTimeBegin").asInstanceOf[Long], dataBlockMap("DataTimeEnd").asInstanceOf[Long])
  //
  //    // step 2: load parseOnline configuration
  //    val fetchTime = LocalDateTime.ofEpochSecond(dataBlockMap("CreationTime").asInstanceOf[Long] / 1000, ((dataBlockMap("CreationTime").asInstanceOf[Long] % 1000) * 1000000).toInt, ZoneOffset.ofHours(8))
  //    val worker = new IFWorker("tcp://127.0.0.1:224")
  //    val storage = worker.blockingInvoker("Storage")
  //    val fetchedOnlineData = storage.get("MDIQKD_GroundTDC", "2020-07-25T15:37:45.318000+08:00", "FetchTime", filter=Map("FetchTime" -> 1, "Data" -> 1)).asInstanceOf[Map[String, Any]]
  //    val fetchedOnlineData_MDIQKDQBER = fetchedOnlineData("Data").asInstanceOf[Map[String, Any]]("MDIQKDQBER").asInstanceOf[Map[String, Any]]
  //    val fetchedOnlineData_MDIQKDQBER_configuration = fetchedOnlineData_MDIQKDQBER("Configuration").asInstanceOf[Map[String, Any]]
  //
  //    // step 3: start a MDIQKD Analysiser
  //    val analyserMDIQKDQBER = new MDIQKDQBERAnalyser(16)
  //    analyserMDIQKDQBER.turnOn(fetchedOnlineData_MDIQKDQBER_configuration)
  //
  //    // step 3.5: plot a Histogram
  //    val analyserMultiHistogram = new MultiHistogramAnalyser(16)
  //    analyserMultiHistogram.turnOn(Map("Sync" -> "8", "Signals" -> List(9), "ViewStart" -> -200000, "ViewStop" -> 200000, "BinCount" -> 1000, "Divide" -> 1))
  //    analyserMultiHistogram.dataIncome(dataBlock) match {
  //      case None => throw new RuntimeException
  //      case Some(result) =>{
  ////        println(result)
  //      }
  //    }
  //
  //    // setep 4: parse a DataBlock
  //    analyserMDIQKDQBER.dataIncome(dataBlock) match {
  //      case None => throw new RuntimeException
  //      case Some(result) => {
  ////        println(result)
  //      }
  //    }
  //  }
  test("Test thin DataBlock.") {
    val dataBlock = {
      val raf = new RandomAccessFile("E:\\MDIQKD_Parse\\DataBlock\\2020-07-25T15-37-45.318.datablock", "r")
      val bytes = new Array[Byte](raf.length().toInt)
      raf.readFully(bytes)
      raf.close()
      val dataBlockMap = MsgpackSerializer.deserialize(bytes).asInstanceOf[Map[String, Any]]
      val content = dataBlockMap("Content").asInstanceOf[List[List[Long]]].map(_.toArray).toArray
      new DataBlock(content, dataBlockMap("CreationTime").asInstanceOf[Long], dataBlockMap("DataTimeBegin").asInstanceOf[Long], dataBlockMap("DataTimeEnd").asInstanceOf[Long])
    }
    dataBlock.serialize()
    println(dataBlock)
  }
}
