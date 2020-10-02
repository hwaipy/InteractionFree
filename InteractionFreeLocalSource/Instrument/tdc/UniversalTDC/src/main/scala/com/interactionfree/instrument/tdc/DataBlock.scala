package com.interactionfree.instrument.tdc

import java.nio.{ByteBuffer, LongBuffer}
import java.util.concurrent.atomic.AtomicReference

import scala.collection.mutable.ListBuffer
import com.interactionfree.NumberTypeConversions._
import com.interactionfree.instrument.tdc.DataBlock.PROTOCOL_V1
import com.interactionfree.{IFException, MsgpackSerializer}

import scala.collection.IterableOnce
import scala.util.Random

object DataBlock {
  private val FINENESS = 100000
  private val DEFAULT_PROTOCOL = PROTOCOL_V1
  val PROTOCOL_V1 = "DataBlock_V1"

  def create(content: Array[Array[Long]], creationTime: Long, dataTimeBegin: Long, dataTimeEnd: Long): DataBlock = {
    val dataBlock = new DataBlock(creationTime, dataTimeBegin, dataTimeEnd, content.map(_.length))
    dataBlock.contentRef set content
    dataBlock
  }

  def generate(generalConfig: Map[String, Long], channelConfig: Map[Int, List[Any]]): DataBlock = {
    val creationTime = generalConfig.get("CreationTime") match {
      case Some(ct) => ct
      case None => System.currentTimeMillis()
    }
    val dataTimeBegin = generalConfig.get("DataTimeBegin") match {
      case Some(dtb) => dtb
      case None => 0
    }
    val dataTimeEnd = generalConfig.get("DataTimeEnd") match {
      case Some(dte) => dte
      case None => 0
    }
    val content = Range(0, 16).toArray.map(channel => channelConfig.get(channel) match {
      case None => Array[Long]()
      case Some(config) => config.head.toString match {
        case "Period" => {
          val count: Int = config(1)
          val period = (dataTimeEnd - dataTimeBegin) / count.toDouble
          Range(0, count).toArray.map(i => (i * period).toLong)
        }
        case "Random" => {
          val count: Int = config(1)
          val averagePeriod = (dataTimeEnd - dataTimeBegin) / count
          val random = new Random()
          val randomGaussians = Range(0, count).toArray.map(_ => (1 + random.nextGaussian() / 3) * averagePeriod)
          val randGaussSumRatio = (dataTimeEnd - dataTimeBegin) / randomGaussians.sum
          val randomDeltas = randomGaussians.map(rg => rg * randGaussSumRatio)
          val deltas = ListBuffer[Long]()
          randomDeltas.foldLeft(0.0)((a, b) => {
            deltas += a.toLong
            a + b
          })
          deltas.toArray
        }
        case "Pulse" => {
          val pulseCount: Int = config(1)
          val eventCount: Int = config(2)
          val sigma: Double = config(3)
          val period = (dataTimeEnd - dataTimeBegin) / pulseCount
          val random = new Random()
          Range(0, eventCount).toArray.map(_ => random.nextInt(pulseCount) * period + (random.nextGaussian() * sigma).toLong).sorted
        }
        case _ => throw new RuntimeException
      }
    })
    create(content, creationTime, dataTimeBegin, dataTimeEnd)
  }

  def deserialize(data: Array[Byte]) = {
    val recovered = MsgpackSerializer.deserialize(data).asInstanceOf[Map[String, Any]]
    if (recovered("Format") != PROTOCOL_V1) throw new IFException(s"Data format not supported: ${recovered("Format")}")
    val sizes = recovered("Sizes").asInstanceOf[IterableOnce[Int]].iterator.toArray
    val dataBlock = new DataBlock(recovered("CreationTime"), recovered("DataTimeBegin"), recovered("DataTimeEnd"), sizes)

    def deserializeAChannel(chData: Array[Byte]): Array[Long] = chData.size match {
      case 0 => Array[Long]()
      case _ => {
        val buffer = ByteBuffer.wrap(chData)
        val longBuffer = LongBuffer.allocate(DataBlock.FINENESS)
        val offset = buffer.getLong()
        longBuffer.put(offset)
        var previous = offset

        while (buffer.hasRemaining) {
          val lengthU = buffer.get()
          val length = lengthU & 0x7F
          val minus = (lengthU & 0x80) > 0
          var delta = 0L
          var i = length - 1
          while (i >= 0) {
            var v = buffer.get().toLong
            if (v < 0) v += 256
            delta += (v << (8 * i))
            i -= 1
          }
          previous += (if (minus) -delta else delta)
          longBuffer.put(previous)
        }
        longBuffer.array().slice(0, longBuffer.position())
      }
    }

    val chDatas = recovered("Content").asInstanceOf[IterableOnce[List[Array[Byte]]]].iterator.toArray
    val content = chDatas.map(chData => Array.concat(chData.map(section => deserializeAChannel(section)): _*))
    dataBlock.contentRef set (if (content.isEmpty) null else content)
    dataBlock
  }
}

class DataBlock private(val creationTime: Long, val dataTimeBegin: Long, val dataTimeEnd: Long, val sizes: Array[Int]) {
  private val contentRef = new AtomicReference[Array[Array[Long]]]()

  def release(): Unit = contentRef set null

  def isReleased: Boolean = contentRef.get == null

  def content: Option[Array[Array[Long]]] = contentRef.get match {
    case null => None
    case c => Some(c)
  }

  def getContent: Array[Array[Long]] = contentRef.get

  def serialize(): Array[Byte] = {

    def serializeAChannel(list: Array[Long]) = list.size match {
      case 0 => Array[Byte]()
      case _ => {
        val buffer = ByteBuffer.allocate(list.length * 8)
        buffer.putLong(list(0))
        var i = 0
        val unit = new Array[Byte](8)
        while (i < list.length - 1) {
          val delta = (list(i + 1) - list(i))
          i += 1
          var value = if (delta >= 0) delta else -delta
          var length = 0
          while (value > 0) {
            unit(7 - length) = (value & 0xFF).toByte
            value >>= 8
            length += 1
          }
          buffer put (length | (if (delta > 0) 0x00 else 0x80)).toByte
          buffer.put(unit, 8 - length, length)
        }
        buffer.array().slice(0, buffer.position())
      }
    }

    val serializedContent = content match {
      case Some(c) => c.map(ch => Range(0, Math.ceil(ch.size / DataBlock.FINENESS.toDouble).toInt).map(i => serializeAChannel(ch.slice(i * DataBlock.FINENESS, (i + 1) * DataBlock.FINENESS))))
      case None => null
    }
    val result = Map(
      "Format" -> PROTOCOL_V1,
      "CreationTime" -> creationTime,
      "DataTimeBegin" -> dataTimeBegin,
      "DataTimeEnd" -> dataTimeEnd,
      "Sizes" -> sizes,
      "Content" -> serializedContent
    )
    System.currentTimeMillis()
    MsgpackSerializer.serialize(result)
  }
}