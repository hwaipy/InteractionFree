package com.interactionfree.instrument.tdc

import java.net.ServerSocket
import java.nio.{ByteBuffer, LongBuffer}
import java.util.concurrent.Executors
import java.util.concurrent.atomic.{AtomicLong, AtomicReference}

import scala.collection.mutable.{ArrayBuffer, ListBuffer}
import scala.concurrent.{ExecutionContext, Future}
import com.interactionfree.NumberTypeConversions._
import com.interactionfree.MsgpackSerializer

import scala.collection.IterableOnce
import scala.util.Random

class TDCProcessServer(val channelCount: Int, port: Int, dataIncome: Any => Unit, adapters: List[TDCDataAdapter], private val localStorePath: String) {
  private val executionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor(r => {
    val t = new Thread(r)
    t.setDaemon(true)
    t
  }))
  private val tdcParser = new TDCParser(new TDCDataProcessor {
    override def process(data: Any): Unit = dataIncome(data)
  }, adapters.toArray)
  private val server = new ServerSocket(port)
  val buffer = new Array[Byte](10000000)
  Future[Any] {
    while (!server.isClosed) {
      val socket = server.accept
      val remoteAddress = socket.getRemoteSocketAddress
      println(s"Connection from $remoteAddress accepted.")
      val totalDataSize = new AtomicLong(0)
      try {
        val in = socket.getInputStream
        while (!socket.isClosed) {
          val read = in.read(buffer)
          if (read < 0) socket.close()
          else {
            totalDataSize.set(totalDataSize.get + read)
            val array = new Array[Byte](read)
            Array.copy(buffer, 0, array, 0, read)
            tdcParser.offer(array)
          }
        }
      } catch {
        case _: Throwable => // e.printStackTrace()
      } finally {
        println(s"End of connection: $remoteAddress. Total Data Size: ${totalDataSize.get}")
      }
    }
  }(executionContext)

  def stop(): Unit = {
    server.close()
    tdcParser.stop()
  }

  //  private val sectionStartTime = new AtomicLong(0)
  //  private var sectionStoredSize = new AtomicLong(0)
  //  private var sectionStoreStream = new AtomicReference[BufferedOutputStream](null)
  //
  //  private def store(data: Array[Byte]) = {
  //    if (sectionStoreStream == null) {
  //      sectionStoreStream set new BufferedOutputStream(new FileOutputStream("TEMP.TDC"))
  //      sectionStartTime set System.currentTimeMillis()
  //    }
  //    //            sectionStoreStream.write(array)
  //    //            sectionStoredSize += read
  //    //            if (sectionStoredSize > 1e7) {
  //    //              sectionStoreStream.close()
  //    //              val currentTime = System.currentTimeMillis()
  //    //              Files.move(new File("TEMP.TDC").toPath, new File(s"${sectionStartTime}-${currentTime}.tdc").toPath, StandardCopyOption.REPLACE_EXISTING)
  //    //              sectionStartTime = currentTime
  //    //              sectionStoreStream = new BufferedOutputStream(new FileOutputStream("TEMP.TDC"))
  //    //              sectionStoredSize = 0
  //    //            }
  //  }
}

class LongBufferToDataBlockListTDCDataAdapter(channelCount: Int) extends TDCDataAdapter {
  private val dataBlocks = new ArrayBuffer[DataBlock]()

  def offer(data: Any): AnyRef = {
    dataBlocks.clear()
    dataIncome(data)
    dataBlocks.toList
  }

  def flush(data: Any): AnyRef = offer(data)

  private def dataIncome(data: Any): Unit = {
    if (!data.isInstanceOf[LongBuffer]) throw new IllegalArgumentException(s"LongBuffer expected, not ${data.getClass}")
    val buffer = data.asInstanceOf[LongBuffer]
    while (buffer.hasRemaining) {
      val item = buffer.get
      val time = item >> 4
      val channel = (item & 0xF).toInt
      feedTimeEvent(channel, time)
    }
  }

  private val timeEvents = Range(0, channelCount).map(_ => ArrayBuffer[Long]()).toList
  private var unitEndTime = Long.MinValue
  private val timeUnitSize = 1000000000000L

  private def feedTimeEvent(channel: Int, time: Long) = {
    if (time > unitEndTime) {
      if (unitEndTime == Long.MinValue) unitEndTime = time
      else flush()
    }
    timeEvents(channel) += time
  }

  private def flush(): Unit = {
    val data = timeEvents.map(_.toArray).toArray
    timeEvents.foreach(_.clear())
    val creationTime = System.currentTimeMillis() - 1000
    dataBlocks += DataBlock.create(data, creationTime, unitEndTime - timeUnitSize, unitEndTime)
    unitEndTime += timeUnitSize
  }
}

object DataBlock {
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
          val randomGaussians = Range(0, count).toArray.map(_ => (random.nextGaussian() / 3 + 1) * averagePeriod)
          val randGaussSumRatio = (dataTimeEnd - dataTimeBegin) / randomGaussians.sum
          val randomDeltas = randomGaussians.map(rg => rg * randGaussSumRatio)
          val deltas = ListBuffer[Long]()
          randomDeltas.foldLeft(0.0)((a, b) => {
            deltas += a.toLong
            a + b
          })
          deltas.toArray
        }
        case _ => throw new RuntimeException
      }
    })
    create(content, creationTime, dataTimeBegin, dataTimeEnd)
  }

  def deserialize(data: Array[Byte]) = {
    val recovered = MsgpackSerializer.deserialize(data).asInstanceOf[Map[String, Any]]
    val sizes = recovered("Sizes").asInstanceOf[IterableOnce[Int]].iterator.toArray
    val dataBlock = new DataBlock(recovered("CreationTime"), recovered("DataTimeBegin"), recovered("DataTimeEnd"), sizes)

    def deserializeAChannel(chData: Array[Byte], size: Int): Array[Long] = chData.size match {
      case 0 => Array[Long]()
      case _ => {
        val buffer = ByteBuffer.wrap(chData)
        val longBuffer = LongBuffer.allocate(size)
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
        longBuffer.array()
      }
    }

    val chDatas = recovered("Content").asInstanceOf[IterableOnce[Array[Byte]]].iterator.toArray
    val content = chDatas.zip(sizes).map(z => deserializeAChannel(z._1, z._2))
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

  //  def store(path: String) = {
  //    val creationTimeISO = LocalDateTime.ofEpochSecond(creationTime / 1000, ((creationTime % 1000) * 1000000).toInt, ZoneOffset.ofHours(8)).toString.replaceAll(":", "-")
  //    val raf = new RandomAccessFile(path + "/" + creationTimeISO + ".datablock", "rw")
  //    val packer = org.msgpack.core.MessagePack.newDefaultBufferPacker
  //    val bytes = MsgpackSerializer.serialize(Map("Content" -> content, "CreationTime" -> creationTime, "DataTimeBegin" -> dataTimeBegin, "DataTimeEnd" -> dataTimeEnd))
  //    raf.write(bytes)
  //    raf.close()
  //  }

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
      case Some(c) => c.map(ch => serializeAChannel(ch))
      case None => null
    }
    val result = Map(
      "CreationTime" -> creationTime,
      "DataTimeBegin" -> dataTimeBegin,
      "DataTimeEnd" -> dataTimeEnd,
      "Sizes" -> sizes,
      "Content" -> serializedContent
    )
    MsgpackSerializer.serialize(result)
  }
}