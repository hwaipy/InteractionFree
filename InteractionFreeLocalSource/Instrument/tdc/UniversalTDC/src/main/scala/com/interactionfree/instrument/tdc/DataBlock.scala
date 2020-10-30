package com.interactionfree.instrument.tdc

import java.nio.{ByteBuffer, LongBuffer}
import java.util.concurrent.atomic.AtomicReference
import scala.collection.mutable.ListBuffer
import com.interactionfree.NumberTypeConversions._
import com.interactionfree.{IFException, MsgpackSerializer}
import scala.collection.IterableOnce
import scala.util.Random

object DataBlock {
  private val FINENESS = 100000
  val PROTOCOL_V1 = "DataBlock_V1"
  private val DEFAULT_PROTOCOL = PROTOCOL_V1

  def create(content: Array[Array[Long]], creationTime: Long, dataTimeBegin: Long, dataTimeEnd: Long, resolution: Double = 1e-12): DataBlock = {
    val dataBlock = new DataBlock(creationTime, dataTimeBegin, dataTimeEnd, content.map(_.length), resolution)
    dataBlock.contentRef set content
    dataBlock
  }

  def generate(generalConfig: Map[String, Long], channelConfig: Map[Int, List[Any]]): DataBlock = {
    val creationTime = generalConfig.get("CreationTime") match {
      case Some(ct) => ct
      case None     => System.currentTimeMillis()
    }
    val dataTimeBegin = generalConfig.get("DataTimeBegin") match {
      case Some(dtb) => dtb
      case None      => 0
    }
    val dataTimeEnd = generalConfig.get("DataTimeEnd") match {
      case Some(dte) => dte
      case None      => 0
    }
    val content = Range(0, 16).toArray.map(channel =>
      channelConfig.get(channel) match {
        case None => Array[Long]()
        case Some(config) =>
          config.head.toString match {
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
      }
    )
    create(content, creationTime, dataTimeBegin, dataTimeEnd)
  }

  def deserialize(data: Array[Byte]) = {
    val recovered = MsgpackSerializer.deserialize(data).asInstanceOf[Map[String, Any]]
    val protocol = recovered("Format").toString()
    if (protocol != PROTOCOL_V1) throw new IFException(s"Data format not supported: ${recovered("Format")}")
    val sizes = recovered("Sizes").asInstanceOf[IterableOnce[Int]].iterator.toArray
    val dataBlock = new DataBlock(recovered("CreationTime"), recovered("DataTimeBegin"), recovered("DataTimeEnd"), sizes, recovered("Resolution"))
    val chDatas = recovered("Content").asInstanceOf[IterableOnce[List[Array[Byte]]]].iterator.toArray
    val content = chDatas.map(chData => Array.concat(chData.map(section => DataBlockSerializers(protocol).deserialize(section)): _*))
    dataBlock.contentRef set (if (content.isEmpty) null else content)
    dataBlock
  }
}

class DataBlock private (val creationTime: Long, val dataTimeBegin: Long, val dataTimeEnd: Long, val sizes: Array[Int], val resolution: Double = 1e-12) {
  private val contentRef = new AtomicReference[Array[Array[Long]]]()

  def release(): Unit = contentRef set null

  def isReleased: Boolean = contentRef.get == null

  def content: Option[Array[Array[Long]]] =
    contentRef.get match {
      case null => None
      case c    => Some(c)
    }

  def getContent: Array[Array[Long]] = contentRef.get

  def serialize(protocol: String = DataBlock.DEFAULT_PROTOCOL): Array[Byte] = {
    val serializedContent = content match {
      case Some(c) => c.map(ch => Range(0, Math.ceil(ch.size / DataBlock.FINENESS.toDouble).toInt).map(i => DataBlockSerializers(protocol).serialize(ch.slice(i * DataBlock.FINENESS, (i + 1) * DataBlock.FINENESS))))
      case None    => null
    }
    val result = Map(
      "Format" -> DataBlock.PROTOCOL_V1,
      "CreationTime" -> creationTime,
      "Resolution" -> resolution,
      "DataTimeBegin" -> dataTimeBegin,
      "DataTimeEnd" -> dataTimeEnd,
      "Sizes" -> sizes,
      "Content" -> serializedContent
    )
    MsgpackSerializer.serialize(result)
  }

  def convertResolution(resolution: Double) = {
    val ratio = this.resolution / resolution
    val newDB = new DataBlock(creationTime, (dataTimeBegin * ratio).toLong, (dataTimeEnd * ratio).toLong, sizes, resolution)
    content.foreach(c => {
      val newContent = c.map(ch => ch.map(n => (n * ratio).toLong))
      newDB.contentRef set newContent
    })
    newDB
  }
}

abstract class DataBlockSerializer {
  def serialize(data: Array[Long]): Array[Byte]
  def deserialize(data: Array[Byte]): Array[Long]
}

object DataBlockSerializers {
  val pv1DBS = new DataBlockSerializer {
    private val MAX_VALUE = 1e16

    def serialize(list: Array[Long]) =
      list.size match {
        case 0 => Array[Byte]()
        case _ => {
          val buffer = ByteBuffer.allocate(list.length * 8)
          buffer.putLong(list(0))

          val unitSize = 15
          val unit = new Array[Byte](unitSize + 1)
          var hasHalfByte = false
          var halfByte: Byte = 0
          var i = 0
          while (i < list.length - 1) {
            val delta = (list(i + 1) - list(i))
            i += 1
            if (delta > MAX_VALUE || delta < -MAX_VALUE) throw new IllegalArgumentException(s"The value to be serialized exceed MAX_VALUE: ${delta}")
            var value = delta
            var length = 0
            var keepGoing = true
            val valueBase = if (delta >= 0) 0 else 0xffffffffffffffffL
            while (keepGoing) {
              unit(unitSize - length) = (value & 0xf).toByte
              value >>= 4
              length += 1
              if (value == valueBase) {
                keepGoing = (unit(unitSize - length + 1) & 0x8) == (if (delta >= 0) 0x8 else 0x0)
              } else if (length >= unitSize) keepGoing = false
            }
            unit(unitSize - length) = length.toByte
            var p = 0
            while (p <= length) {
              if (hasHalfByte) buffer.put(((halfByte << 4) | unit(unitSize - length + p)).toByte) else halfByte = unit(unitSize - length + p)
              hasHalfByte = !hasHalfByte
              p += 1
            }
          }
          if (hasHalfByte) buffer.put((halfByte << 4).toByte)
          buffer.array().slice(0, buffer.position())
        }
      }

    def deserialize(data: Array[Byte]): Array[Long] =
      data.size match {
        case 0 => Array[Long]()
        case _ => {
          val offset = (ByteBuffer.wrap(data.slice(0, 8))).getLong()
          val longBuffer = LongBuffer.allocate(data.length)
          longBuffer.put(offset)
          var previous = offset

          var positionC = 8
          var positionF = 0
          def hasNext = positionC < data.length
          def getNext = {
            val b = data(positionC)
            if (positionF == 0) {
              positionF = 1
              (b >> 4) & 0xf
            } else {
              positionF = 0
              positionC += 1
              b & 0xf
            }
          }

          while (hasNext) {
            var length = getNext - 1
            if (length >= 0) {
              var value: Long = (getNext & 0xf)
              if ((value & 0x8) == 0x8) value |= 0xfffffffffffffff0L
              while (length > 0) {
                value <<= 4
                value |= (getNext & 0xf)
                length -= 1
              }
              previous += value
              longBuffer.put(previous)
            }
          }
          longBuffer.array().slice(0, longBuffer.position())
        }
      }
  }
  private val DBS = Map(
    // "NAIVE" -> naiveDBS,
    DataBlock.PROTOCOL_V1 -> pv1DBS
  )

  def apply(name: String) = DBS(name)
}
