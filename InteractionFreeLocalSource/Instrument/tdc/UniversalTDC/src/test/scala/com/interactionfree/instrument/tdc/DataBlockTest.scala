package com.interactionfree.instrument.tdc

import org.scalatest.BeforeAndAfter
import org.scalatest.funsuite.AnyFunSuite

import scala.language.postfixOps
import scala.util.Random

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
    assert(testDataBlock.getContent(0).length == 10000)
    assert(testDataBlock.getContent(1).length == 230000)
    assert(testDataBlock.getContent(5).length == 105888)
    assert(testDataBlock.getContent(10).length == 10)
    assert(testDataBlock.getContent(10)(5) - testDataBlock.getContent(10)(4) == 100000000000L)
    testDataBlock.release()
    assert(testDataBlock.content.isEmpty)
    assert(testDataBlock.isReleased)
    assert(testDataBlock.sizes(0) == 10000)
    assert(testDataBlock.sizes(1) == 230000)
    assert(testDataBlock.sizes(5) == 105888)
    assert(testDataBlock.sizes(10) == 10)
    assert(testDataBlock.sizes(11) == 0)
  }

  test("Test DataBlock serialization and deserialization.") {
    val testDataBlock = DataBlock.generate(
      Map("CreationTime" -> 100, "DataTimeBegin" -> 10, "DataTimeEnd" -> 1000000000010L),
      Map(
        0 -> List("Period", 10000),
        1 -> List("Random", 230000),
        5 -> List("Random", 105888),
        10 -> List("Period", 10),
        12 -> List("Random", 1)
      )
    )
    val binary = testDataBlock.serialize()
    val recoveredDataBlock = DataBlock.deserialize(binary)
    assert(testDataBlock.creationTime == recoveredDataBlock.creationTime)
    assert(testDataBlock.dataTimeBegin == recoveredDataBlock.dataTimeBegin)
    assert(testDataBlock.dataTimeEnd == recoveredDataBlock.dataTimeEnd)
    assert(testDataBlock.sizes.toList == recoveredDataBlock.sizes.toList)
    Range(0, testDataBlock.sizes.length).map(ch => {
      val testDataBlockChannel = testDataBlock.getContent(ch).toList
      val recoveredDataBlockChannel = recoveredDataBlock.getContent(ch).toList
      assert(testDataBlock.sizes(ch) == recoveredDataBlockChannel.size)
      (testDataBlockChannel zip recoveredDataBlockChannel).foreach(z => assert(z._1 == z._2))
    })
  }

  test("Test DataBlock serialization and deserialization with randomized data.") {
    val testDataBlock = DataBlock.create({
      val r = new Random()
      Array(Range(0, 10000).map(_ => r.nextLong(1000000000000L)).toArray)
    }, 100001, 0, 1000000000000L)
    val binary = testDataBlock.serialize()
    val recoveredDataBlock = DataBlock.deserialize(binary)
    assert(testDataBlock.creationTime == recoveredDataBlock.creationTime)
    assert(testDataBlock.dataTimeBegin == recoveredDataBlock.dataTimeBegin)
    assert(testDataBlock.dataTimeEnd == recoveredDataBlock.dataTimeEnd)
    assert(testDataBlock.sizes.toList == recoveredDataBlock.sizes.toList)
    Range(0, testDataBlock.sizes.length).map(ch => {
      val testDataBlockChannel = testDataBlock.getContent(ch).toList
      val recoveredDataBlockChannel = recoveredDataBlock.getContent(ch).toList
      assert(testDataBlock.sizes(ch) == recoveredDataBlockChannel.size)
      (testDataBlockChannel zip recoveredDataBlockChannel).foreach(z => assert(z._1 == z._2))
    })
  }

  test("Test DataBlock serialization and deserialization with totally reversed data.") {
    val testDataBlock = DataBlock.create({
      val r = new Random()
      Array(Range(0, 10000).map(i => i * 100000000L).toArray.reverse)
    }, 100001, 0, 1000000000000L)
    val binary = testDataBlock.serialize()
    val recoveredDataBlock = DataBlock.deserialize(binary)
    assert(testDataBlock.creationTime == recoveredDataBlock.creationTime)
    assert(testDataBlock.dataTimeBegin == recoveredDataBlock.dataTimeBegin)
    assert(testDataBlock.dataTimeEnd == recoveredDataBlock.dataTimeEnd)
    assert(testDataBlock.sizes.toList == recoveredDataBlock.sizes.toList)
    Range(0, testDataBlock.sizes.length).map(ch => {
      val testDataBlockChannel = testDataBlock.getContent(ch).toList
      val recoveredDataBlockChannel = recoveredDataBlock.getContent(ch).toList
      assert(testDataBlock.sizes(ch) == recoveredDataBlockChannel.size)
      (testDataBlockChannel zip recoveredDataBlockChannel).foreach(z => assert(z._1 == z._2))
    })
  }

  test("Test DataBlock serialization and deserialization with released DataBlock.") {
    val testDataBlock = DataBlock.generate(
      Map("CreationTime" -> 100, "DataTimeBegin" -> 10, "DataTimeEnd" -> 1000000000010L),
      Map(
        0 -> List("Period", 10000),
        1 -> List("Random", 230000),
        5 -> List("Random", 105888),
        10 -> List("Period", 10),
        12 -> List("Random", 1)
      )
    )
    testDataBlock.release()
    val binary = testDataBlock.serialize()
    val recoveredDataBlock = DataBlock.deserialize(binary)
    assert(testDataBlock.creationTime == recoveredDataBlock.creationTime)
    assert(testDataBlock.dataTimeBegin == recoveredDataBlock.dataTimeBegin)
    assert(testDataBlock.dataTimeEnd == recoveredDataBlock.dataTimeEnd)
    assert(testDataBlock.sizes.toList == recoveredDataBlock.sizes.toList)
    assert(testDataBlock.getContent == null)
    assert(recoveredDataBlock.getContent == null)
  }
}
