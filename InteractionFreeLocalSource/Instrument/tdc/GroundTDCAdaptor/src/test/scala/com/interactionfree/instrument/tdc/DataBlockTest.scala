package com.interactionfree.instrument.tdc

import java.io.RandomAccessFile
import java.time.{LocalDateTime, ZoneOffset}

import com.interactionfree.{IFWorker, Invocation, MsgpackSerializer}
import org.scalatest.BeforeAndAfter
import org.scalatest.funsuite.AnyFunSuite

import scala.language.postfixOps

class DataBlockTest extends AnyFunSuite with BeforeAndAfter {

  test("Test DataBlock generation.") {
    val testDataBlock = DataBlock.generate(
      Map("CreationTime" -> 100, "DataTimeBegin" -> 10, "DataTimeEnd" -> 1000000000010L),
      Map(
        0 -> List("Period", 10000),
        1 -> List("Random", 230000),
        5 -> List("Random", 105888),
        10 -> List("Period", 10)
      )
    )
    assert(testDataBlock.content.isDefined)
    assert(!testDataBlock.isReleased)
    assert(testDataBlock.getContent(0).size == 10000)
    assert(testDataBlock.getContent(1).size == 230000)
    assert(testDataBlock.getContent(5).size == 105888)
    assert(testDataBlock.getContent(10).size == 10)
    assert(testDataBlock.getContent(10)(5) - testDataBlock.getContent(10)(4) == 100000000000L)
    testDataBlock.release()
    assert(!testDataBlock.content.isDefined)
    assert(testDataBlock.isReleased)
    assert(testDataBlock.sizes(0) == 10000)
    assert(testDataBlock.sizes(1) == 230000)
    assert(testDataBlock.sizes(5) == 105888)
    assert(testDataBlock.sizes(10) == 10)
    assert(testDataBlock.sizes(11) == 0)
  }

  test("Test DataBlock serialization.") {
    val testDataBlock = DataBlock.generate(
      Map("CreationTime" -> 100, "DataTimeBegin" -> 10, "DataTimeEnd" -> 1000000000010L),
      Map(
        0 -> List("Period", 10000),
        1 -> List("Random", 230000),
        5 -> List("Random", 105888),
        10 -> List("Period", 10)
      )
    )

    val t1 = System.nanoTime()
    Range(0, 100).foreach(_ => testDataBlock.serialize())
    val t2 = System.nanoTime()
    println(f"${(t2 - t1) / 1e6 / 100}%.1f ms")
  }
}
