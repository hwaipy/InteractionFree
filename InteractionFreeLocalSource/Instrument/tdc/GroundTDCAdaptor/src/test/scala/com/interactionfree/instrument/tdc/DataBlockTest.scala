package com.interactionfree.instrument.tdc

import java.io.RandomAccessFile
import java.time.{LocalDateTime, ZoneOffset}

import com.interactionfree.{IFWorker, Invocation, MsgpackSerializer}
import org.scalatest.BeforeAndAfter
import org.scalatest.funsuite.AnyFunSuite

import scala.language.postfixOps

class DataBlockTest extends AnyFunSuite with BeforeAndAfter {
  test("Test thin DataBlock.") {
    //    val dataBlock = {
    //      val raf = new RandomAccessFile("E:\\MDIQKD_Parse\\DataBlock\\2020-07-25T15-37-45.318.datablock", "r")
    //      val bytes = new Array[Byte](raf.length().toInt)
    //      raf.readFully(bytes)
    //      raf.close()
    //      val dataBlockMap = MsgpackSerializer.deserialize(bytes).asInstanceOf[Map[String, Any]]
    //      val content = dataBlockMap("Content").asInstanceOf[List[List[Long]]].map(_.toArray).toArray
    //      new DataBlock(content, dataBlockMap("CreationTime").asInstanceOf[Long], dataBlockMap("DataTimeBegin").asInstanceOf[Long], dataBlockMap("DataTimeEnd").asInstanceOf[Long])
    //    }
    //    dataBlock.serialize()
    //    println(dataBlock)
    println("dataBlock")
  }
}
