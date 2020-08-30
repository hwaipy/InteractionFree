package com.interactionfree.instrument.tdc

import scala.collection.mutable.ArrayBuffer
import scala.concurrent.Future
import java.io.{BufferedOutputStream, FileOutputStream, RandomAccessFile}
import java.net.ServerSocket
import java.nio.{ByteBuffer, LongBuffer}
import java.nio.file.Paths
import java.nio.file.Files
import java.time.{LocalDateTime, ZoneOffset}
import java.util.concurrent.{Executors, LinkedBlockingQueue}
import java.util.concurrent.atomic.{AtomicBoolean, AtomicInteger, AtomicLong, AtomicReference}

import scala.jdk.CollectionConverters._
import scala.collection.mutable
import scala.collection.mutable.{ArrayBuffer, ListBuffer}
import scala.concurrent.{ExecutionContext, Future}
import com.interactionfree.NumberTypeConversions._
import org.msgpack.core.MessagePack
import com.interactionfree.{Invocation, Message, MsgpackSerializer}

import scala.util.Random

class TDCProcessServer(val channelCount: Int, port: Int, dataIncome: Any => Unit, adapters: List[TDCDataAdapter], private val localStorePath: String) {
  private val executionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor((r) => {
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
      println(s"Connection from ${remoteAddress} accepted.")
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
        case e: Throwable => // e.printStackTrace()
      } finally {
        println(s"End of connection: ${remoteAddress}. Total Data Size: ${totalDataSize.get}")
      }
    }
  }(executionContext)

  def stop() = {
    server.close
    tdcParser.stop
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

  private def dataIncome(data: Any) = {
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

  private def flush() = {
    val data = timeEvents.map(_.toArray).toArray
    timeEvents.foreach(_.clear())
    val creationTime = System.currentTimeMillis() - 1000
    dataBlocks += DataBlock.create(data, creationTime, unitEndTime - timeUnitSize, unitEndTime)
    unitEndTime += timeUnitSize
  }
}

object DataBlock {
  def create(content: Array[Array[Long]], creationTime: Long, dataTimeBegin: Long, dataTimeEnd: Long) = {
    val dataBlock = new DataBlock(creationTime, dataTimeBegin, dataTimeEnd, content.map(_.size))
    dataBlock.contentRef set content
    dataBlock
  }

  def generate(generalConfig: Map[String, Long], channelConfig: Map[Int, List[Any]]) = {
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
      case Some(config) => config(0).toString match {
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
}

class DataBlock private(val creationTime: Long, val dataTimeBegin: Long, val dataTimeEnd: Long, val sizes: Array[Int]) {
  private val contentRef = new AtomicReference[Array[Array[Long]]]()

  def release() = contentRef set null

  def isReleased = contentRef.get == null

  def content = contentRef.get match {
    case null => None
    case c => Some(c)
  }

  def getContent = contentRef.get

  //  def store(path: String) = {
  //    val creationTimeISO = LocalDateTime.ofEpochSecond(creationTime / 1000, ((creationTime % 1000) * 1000000).toInt, ZoneOffset.ofHours(8)).toString.replaceAll(":", "-")
  //    val raf = new RandomAccessFile(path + "/" + creationTimeISO + ".datablock", "rw")
  //    val packer = org.msgpack.core.MessagePack.newDefaultBufferPacker
  //    val bytes = MsgpackSerializer.serialize(Map("Content" -> content, "CreationTime" -> creationTime, "DataTimeBegin" -> dataTimeBegin, "DataTimeEnd" -> dataTimeEnd))
  //    raf.write(bytes)
  //    raf.close()
  //  }
  //
  def serialize() = {

    def serializeAChannel(list: Array[Long]) = {
      //      println(s"serializing a channel: ${list.size}")
      // deal with length == 0 or 1
      val offset = list(0)
      val deltas = Range(0, list.size - 1).toArray.map(i => list(i + 1) - list(i)) // 5ms // val deltas = list.drop(1).zip(list.dropRight(1)).map(z => z._1 - z._2) // 16ms
      val buffer = ByteBuffer.allocate(list.size * 8)
      //      val buffer = new ArrayBuffer[Byte]()
      val unit = new Array[Byte](8)
      val lengths = deltas.map(delta => {
        var value = if (delta >= 0) delta else -delta
        var length = 0
        while (value > 0) {
          unit(length) = (value & 0xFF).toByte
          value >>= 8
          length += +1
        }
        buffer put length.toByte
        Range(0, length).foreach(i => buffer put unit(length - 1 - i))
        length
      })
      //      println(buffer.position() / 1.0 / list.size)
      //      buffer.toArray
      buffer.array().slice(0, buffer.position())
    } 

    serializeAChannel(getContent(0))
    serializeAChannel(getContent(1))
    //    serializeAChannel(content(8))
  }
}