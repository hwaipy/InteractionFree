package com.interactionfree.instrument.tdc

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
import com.interactionfree.instrument.tdc.local.LocalTDCDataFeeder
import org.msgpack.core.MessagePack
import com.interactionfree.{Invocation, Message, MsgpackSerializer}

class TDCProcessServer(val channelCount: Int, port: Int, dataIncome: Any => Unit, adapters: List[TDCDataAdapter], private val localStorePath: String) {
  private val executionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor((r) => {
    val t = new Thread(r)
    t.setDaemon(true)
    t
  }))
  private val tdcParser = new TDCParser(new TDCDataProcessor {
    override def process(data: Any): Unit = dataIncome(data)
  }, adapters.toArray)
  private val storableBuffer = new StorableBuffer(tdcParser, localStorePath)
  private val server = new ServerSocket(port)
  private val finishedConnections = new AtomicInteger(0)

  def getFinishedConnections = finishedConnections.get

  def setLocalBufferPermenent(p: Boolean) = storableBuffer.setLocalBufferPermenent(p)

  def isLocalBufferPermenent() = storableBuffer.isLocalBufferPermenent()

  val buffer = new Array[Byte](StorableBuffer.UNIT_CAPACITY)
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
            //  store(array)
            //            tdcParser.offer(array)
            storableBuffer.offer(array)
          }
        }
      } catch {
        case e: Throwable => e.printStackTrace()
      } finally {
        println(s"End of connection: ${remoteAddress}. Total Data Size: ${totalDataSize.get}")
      }
      finishedConnections.incrementAndGet()
    }
  }(executionContext)

  def stop() = {
    server.close
    storableBuffer.stop()
    tdcParser.stop
  }

  private val sectionStartTime = new AtomicLong(0)
  private var sectionStoredSize = new AtomicLong(0)
  private var sectionStoreStream = new AtomicReference[BufferedOutputStream](null)

  private def store(data: Array[Byte]) = {
    if (sectionStoreStream == null) {
      sectionStoreStream set new BufferedOutputStream(new FileOutputStream("TEMP.TDC"))
      sectionStartTime set System.currentTimeMillis()
    }
    //            sectionStoreStream.write(array)
    //            sectionStoredSize += read
    //            if (sectionStoredSize > 1e7) {
    //              sectionStoreStream.close()
    //              val currentTime = System.currentTimeMillis()
    //              Files.move(new File("TEMP.TDC").toPath, new File(s"${sectionStartTime}-${currentTime}.tdc").toPath, StandardCopyOption.REPLACE_EXISTING)
    //              sectionStartTime = currentTime
    //              sectionStoreStream = new BufferedOutputStream(new FileOutputStream("TEMP.TDC"))
    //              sectionStoredSize = 0
    //            }
  }
}

object StorableBuffer {
  val UNIT_CAPACITY = 10 * 1000 * 1000
}

class StorableBuffer(private val parser: TDCParser, private val storagePath: String) {

  object BufferEntry {
    val STORAGE_INDEX = new AtomicInteger(0)
  }

  class BufferEntry {
    private val usedDataList = new ListBuffer[Array[Byte]]
    private val unusedDataList = new ListBuffer[Array[Byte]]
    private val creationTimeISO = LocalDateTime.now().toString.split("\\.")(0).replaceAll(":", "").replaceAll("-", "").replaceAll("T", "")
    private val dumped = new AtomicBoolean(false)
    val inMemory = new AtomicBoolean(true)
    private val storageIndex = BufferEntry.STORAGE_INDEX.getAndIncrement()

    private val storedSize = new AtomicInteger(0)

    def dataSize = if (inMemory.get) unusedDataList.map(_.size).sum + usedDataList.map(_.size).sum else storedSize.get

    def remaining = StorableBuffer.UNIT_CAPACITY - dataSize

    def offer(data: Array[Byte]) = {
      if (dumped.get) throw new IllegalStateException("Can not offer data to a dumped BufferEntry.")
      if (remaining < data.size) throw new IllegalStateException("No enough room in BufferEntry.")
      unusedDataList += data
    }

    val filePath = Paths.get(storagePath, s"${creationTimeISO}_${storageIndex}.gtdc").toString

    def dump() = if (!dumped.get) {
      inMemory set false
      dumped set true
      val raf = new RandomAccessFile(filePath, "rw")
      usedDataList.foreach(raf.write)
      unusedDataList.foreach(raf.write)
      raf.close()
      usedDataList.clear()
      unusedDataList.clear()
      //      println("dump")
    }

    def delete() = Files.deleteIfExists(Paths.get(filePath))

    def load() = if (!inMemory.get) {
      inMemory set true
      val raf = new RandomAccessFile(filePath, "rw")
      val data = new Array[Byte](raf.length())
      raf.readFully(data)
      unusedDataList += data
      raf.close()
    }

    def hasUnusedData() = unusedDataList.size > 0

    def getNextUnusedData() = {
      val data = unusedDataList.remove(0)
      usedDataList += data
      data
    }
  }

  private val bufferPermenent = new AtomicBoolean(false)

  def setLocalBufferPermenent(p: Boolean) = bufferPermenent set p

  def isLocalBufferPermenent() = bufferPermenent.get

  private val stoped = new AtomicBoolean(false)
  private val incomingQueue = new LinkedBlockingQueue[Array[Byte]]()
  //  private val parsingQueue = new LinkedBlockingQueue[Array[Byte]]()
  private val bufferEntryList = new ListBuffer[BufferEntry]()
  bufferEntryList += new BufferEntry

  def offer(data: Array[Byte]) = incomingQueue.offer(data)

  def stop() = stoped set true

  def dealInput() = {
    // step 1: merge data in incomingQueue into bufferEntryList
    while (incomingQueue.size > 0) {
      val incomingData = incomingQueue.take()
      if (bufferEntryList.last.remaining < incomingData.size) bufferEntryList += new BufferEntry()
      bufferEntryList.last.offer(incomingData)
    }
    // step 2: if bufferEntryList has more than 3 items, dump [2:-1]
    if (bufferEntryList.size > 3) bufferEntryList.slice(2, bufferEntryList.size - 1).foreach(_.dump())
    // step 3: load the first two items of bufferEntryList
    bufferEntryList.slice(0, 2).foreach(_.load())
    // step 4: if there is unsed data in the first item, and data in parsingQueue is less than UNIT_CAPACITY, then append an unsed data to parsingQueue
    while (bufferEntryList.head.hasUnusedData() && parser.bufferedDataSize() < StorableBuffer.UNIT_CAPACITY) {
      val nextUnusedData = bufferEntryList.head.getNextUnusedData()
      parser.offer(nextUnusedData)
      //      storeForTest(nextUnusedData)
    }
    // step 5: if the first item in bufferEntryList is used up, dump and drop.
    if (bufferEntryList.size >= 2 && !bufferEntryList.head.hasUnusedData()) {
      val item = bufferEntryList.remove(0)
      item.dump()
      if (!bufferPermenent.get) item.delete()
    }
  }

  Future[Any] {
    while (!stoped.get) {
      try {
        dealInput()
        //        println(s"${bufferEntryList.map(_.dataSize).sum}    ${bufferEntryList.size}    ${bufferEntryList.map(_.inMemory).mkString(" ")}")
        Thread.sleep(100)
      } catch {
        case e: InterruptedException =>
        case e: Throwable => e.printStackTrace()
      }
    }
  }(ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor((r) => {
    val t = new Thread(r)
    t.setDaemon(true)
    t
  })))

  //  private def storeForTest(data: Array[Byte]) = {
  //    val raf = new RandomAccessFile(storagePath + "/output.tdc", "rw")
  //    raf.skipBytes(raf.length())
  //    raf.write(data)
  //    raf.close()
  //  }
}

class LongBufferToDataBlockListTDCDataAdapter(channelCount: Int) extends TDCDataAdapter {
  val delays = Range(0, channelCount).map(_ => 0L).toArray
  private val dataBlocks = new ArrayBuffer[DataBlock]()

  def offer(data: Any): AnyRef = {
    dataBlocks.clear()
    dataIncome(data)
    dataBlocks.toList
  }

  def flush(data: Any): AnyRef = offer(data)

  def setDelays(delays: List[Long]) = {
    if (delays.size != this.delays.size) throw new IllegalArgumentException(s"Delays should has length of ${this.delays.size}.")
    delays.zipWithIndex.foreach(z => this.delays(z._2) = z._1)
  }

  def setDelay(channel: Int, delay: Long) = {
    if (channel >= this.delays.size || channel < 0) throw new IllegalArgumentException(s"Channel $channel out of range.")
    delays(channel) = delay
  }

  def getDelays() = delays.toList

  private def dataIncome(data: Any) = {
    if (!data.isInstanceOf[LongBuffer]) throw new IllegalArgumentException(s"LongBuffer expected, not ${data.getClass}")
    val buffer = data.asInstanceOf[LongBuffer]
    //    if (buffer.limit() > 0) println(s"${buffer.limit()} timeevents income.")
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
    //    if (channel < 4 && channel > 0) println(time)
    if (time > unitEndTime) {
      if (unitEndTime == Long.MinValue) unitEndTime = time
      else flush()
    }
    timeEvents(channel) += time
  }

  private def flush() = {
    val data = timeEvents.zipWithIndex.map(z => z._1.toArray.map(t => t + delays(z._2))).toArray
    timeEvents.foreach(_.clear())
    val creationTime = if (GroundTDC.LOCAL) LocalTDCDataFeeder.getNextLocalDataBlockCreationTime else System.currentTimeMillis()
    dataBlocks += new DataBlock(data, creationTime, unitEndTime - timeUnitSize, unitEndTime)
    unitEndTime += timeUnitSize
  }
}

class DataBlock(val content: Array[Array[Long]], val creationTime: Long, val dataTimeBegin: Long, val dataTimeEnd: Long) {
  def store(path: String) = {
    val creationTimeISO = LocalDateTime.ofEpochSecond(creationTime / 1000, ((creationTime % 1000) * 1000000).toInt, ZoneOffset.ofHours(8)).toString.replaceAll(":", "-")
    val raf = new RandomAccessFile(path + "/" + creationTimeISO + ".datablock", "rw")
    val packer = org.msgpack.core.MessagePack.newDefaultBufferPacker
    val bytes = MsgpackSerializer.serialize(Map("Content" -> content, "CreationTime" -> creationTime, "DataTimeBegin" -> dataTimeBegin, "DataTimeEnd" -> dataTimeEnd))
    raf.write(bytes)
    raf.close()
  }

  def serialize() = {
    val t1 = System.nanoTime()

    def serializeAChannel(list: Array[Long]) = {
      println(s"serializing a channel: ${list.size}")
      //      println(s"serializing a list: ${list.size}")
      val offset = list.min
      val deltas = list.drop(1).zip(list.dropRight(1)).map(z => z._1 - z._2)
      val buffer = ArrayBuffer[Byte]()
      val unit = new Array[Byte](8)
      val lengths = deltas.map(d => {
        var value = d
        var length = 0
        while (value > 0) {
          unit(length) = (value & 0xFF).toByte
          value >>= 8
          length += +1
        }
        buffer addOne length.toByte
        Range(0, length).foreach(i => buffer addOne unit(length - 1 - i))
        length
      })


      println(buffer.size / 1.0 / list.size)
    }

    serializeAChannel(content(0))
    serializeAChannel(content(4))
    serializeAChannel(content(8))

    val t2 = System.nanoTime()
    println(f"${(t2 - t1) / 1e6}%.1f ms")
  }
}

abstract class DataAnalyser {
  protected val on = new AtomicBoolean(false)
  protected val configuration = new mutable.HashMap[String, Any]()

  def dataIncome(dataBlock: DataBlock): Option[Map[String, Any]] = if (on.get) Some(analysis(dataBlock) ++ Map("Configuration" -> configuration)) else None

  def turnOn(paras: Map[String, Any]) = {
    on.set(true)
    configure(paras)
  }

  def turnOff() = on.set(false)

  protected def analysis(dataBlock: DataBlock): Map[String, Any]

  def configure(paras: Map[String, Any]): Unit = paras.foreach(e => if (configure(e._1, e._2)) configuration(e._1) = e._2)

  protected def configure(key: String, value: Any): Boolean = true

  def getConfiguration() = configuration.toMap

  def isTurnedOn() = on.get
}

class CounterAnalyser(channelCount: Int) extends DataAnalyser {

  override protected def analysis(dataBlock: DataBlock) = Range(0, dataBlock.content.size).map(_.toString()).zip(dataBlock.content.map(list => list.size)).toMap
}

//class HistogramAnalyser(channelCount: Int) extends DataAnalyser {
//  configuration("Sync") = 1
//  configuration("SyncFrac") = 1
//  configuration("Signal") = 1
//  configuration("ViewStart") = -100000
//  configuration("ViewStop") = 100000
//  configuration("BinCount") = 1000
//  configuration("Divide") = 1
//
//  override def configure(key: String, value: Any) = {
//    key match {
//      case "Sync" => {
//        val sc: Int = value
//        sc >= 0 && sc < channelCount
//      }
//      case "SyncFrac" => {
//        val sc: Int = value
//        sc > 0
//      }
//      case "Signal" => {
//        val sc: Int = value
//        sc >= 0 && sc < channelCount
//      }
//      case "ViewStart" => true
//      case "ViewStop" => true
//      case "BinCount" => {
//        val sc: Int = value
//        sc > 0 && sc < 2000
//      }
//      case "Divide" => {
//        val sc: Int = value
//        sc > 0
//      }
//      case _ => false
//    }
//  }
//
//  override protected def analysis(dataBlock: DataBlock) = {
//    val deltas = new ArrayBuffer[Long]()
//    val syncChannel: Int = configuration("Sync")
//    val syncFrac: Int = configuration("SyncFrac")
//    val signalChannel: Int = configuration("Signal")
//    val viewStart: Long = configuration("ViewStart")
//    val viewStop: Long = configuration("ViewStop")
//    val binCount: Int = configuration("BinCount")
//    val divide: Int = configuration("Divide")
//    val tList = dataBlock.content(syncChannel).zipWithIndex.filter(_._2 % syncFrac == 0).map(_._1)
//    val sList = dataBlock.content(signalChannel)
//    val viewFrom = viewStart
//    val viewTo = viewStop
//    if (tList.size > 0 && sList.size > 0) {
//      var preStartT = 0
//      val lengthT = tList.size
//      sList.foreach(s => {
//        var cont = true
//        while (preStartT < lengthT && cont) {
//          val t = tList(preStartT)
//          val delta = s - t
//          if (delta > viewTo) {
//            preStartT += 1
//          } else cont = false
//        }
//        var tIndex = preStartT
//        cont = true
//        while (tIndex < lengthT && cont) {
//          val t = tList(tIndex)
//          val delta = s - t
//          if (delta > viewFrom) {
//            deltas += delta
//            tIndex += 1
//          } else cont = false
//        }
//      })
//    }
//    val histo = new Histogram(deltas.toArray, binCount, viewFrom, viewTo, divide)
//    Map[String, Any]("SyncChannel" -> syncChannel, "SignalChannel" -> signalChannel,
//      "ViewFrom" -> viewFrom, "ViewTo" -> viewTo, "Divide" -> divide, "Histogram" -> histo.yData.toList)
//  }
//}

class MultiHistogramAnalyser(channelCount: Int) extends DataAnalyser {
  configuration("Sync") = 0
  configuration("Signals") = List(1)
  configuration("ViewStart") = -100000
  configuration("ViewStop") = 100000
  configuration("BinCount") = 1000
  configuration("Divide") = 1

  override def configure(key: String, value: Any) = {
    key match {
      case "Sync" => {
        val sc: Int = value
        sc >= 0 && sc < channelCount
      }
      case "Signals" => {
        val sc: List[Int] = value.asInstanceOf[List[Int]]
        sc.forall(c => c >= 0 && c < channelCount)
      }
      case "ViewStart" => true
      case "ViewStop" => true
      case "BinCount" => {
        val sc: Int = value
        sc > 0 && sc < 2000
      }
      case "Divide" => {
        val sc: Int = value
        sc > 0
      }
      case _ => false
    }
  }

  override protected def analysis(dataBlock: DataBlock) = {
    val syncChannel: Int = configuration("Sync")
    val signalChannels = configuration("Signals").asInstanceOf[List[Int]]
    val viewStart: Long = configuration("ViewStart")
    val viewStop: Long = configuration("ViewStop")
    val binCount: Int = configuration("BinCount")
    val divide: Int = configuration("Divide")
    val tList = dataBlock.content(syncChannel)
    val viewFrom = viewStart
    val viewTo = viewStop
    val histograms = signalChannels.map(signalChannel => {
      val deltas = new ArrayBuffer[Long]()
      val sList = dataBlock.content(signalChannel)
      if (tList.size > 0 && sList.size > 0) {
        var preStartT = 0
        val lengthT = tList.size
        sList.foreach(s => {
          var cont = true
          while (preStartT < lengthT && cont) {
            val t = tList(preStartT)
            val delta = s - t
            if (delta > viewTo) {
              preStartT += 1
            } else cont = false
          }
          var tIndex = preStartT
          cont = true
          while (tIndex < lengthT && cont) {
            val t = tList(tIndex)
            val delta = s - t
            if (delta > viewFrom) {
              deltas += delta
              tIndex += 1
            } else cont = false
          }
        })
      }
      new Histogram(deltas.toArray, binCount, viewFrom, viewTo, divide).yData.toList
    })
    Map[String, Any]("Histograms" -> histograms)
  }
}

class CoincidenceHistogramAnalyser(channelCount: Int) extends DataAnalyser {
  configuration("ChannelA") = 0
  configuration("ChannelB") = 1
  configuration("ViewStart") = -100000
  configuration("ViewStop") = 100000
  configuration("BinCount") = 1000

  override def configure(key: String, value: Any) = {
    key match {
      case "ChannelA" => {
        val sc: Int = value
        sc >= 0 && sc < channelCount
      }
      case "ChannelB" => {
        val sc: Int = value
        sc >= 0 && sc < channelCount
      }
      case "ViewStart" => true
      case "ViewStop" => true
      case "BinCount" => {
        val sc: Int = value
        sc > 0 && sc < 2000
      }
      case _ => false
    }
  }

  override protected def analysis(dataBlock: DataBlock) = {
    val deltas = new ArrayBuffer[Long]()
    val syncChannel: Int = configuration("ChannelA")
    val signalChannel: Int = configuration("ChannelB")
    val viewStart: Long = configuration("ViewStart")
    val viewStop: Long = configuration("ViewStop")
    val binCount: Int = configuration("BinCount")
    val tList = dataBlock.content(syncChannel)
    val sList = dataBlock.content(signalChannel)
    val viewFrom = viewStart
    val viewTo = viewStop
    if (tList.size > 0 && sList.size > 0) {
      var preStartT = 0
      val lengthT = tList.size
      sList.foreach(s => {
        var cont = true
        while (preStartT < lengthT && cont) {
          val t = tList(preStartT)
          val delta = s - t
          if (delta > viewTo) {
            preStartT += 1
          } else cont = false
        }
        var tIndex = preStartT
        cont = true
        while (tIndex < lengthT && cont) {
          val t = tList(tIndex)
          val delta = s - t
          if (delta > viewFrom) {
            deltas += delta
            tIndex += 1
          } else cont = false
        }
      })
    }
    val histo = new Histogram(deltas.toArray, binCount, viewFrom, viewTo, 1)
    Map[String, Any]("Histogram" -> histo.yData.toList)
  }
}

class Histogram(deltas: Array[Long], binCount: Int, viewFrom: Long, viewTo: Long, divide: Int) {
  val min = viewFrom.toDouble
  val max = viewTo.toDouble
  val binSize = (max - min) / binCount / divide
  val xData = Range(0, binCount).map(i => (i * binSize + min) + binSize / 2).toArray
  val yData = new Array[Int](binCount)
  deltas.foreach(delta => {
    val deltaDouble = delta.toDouble
    if (deltaDouble < min) {
      /* this data is smaller than min */
    } else if (deltaDouble == max) { // the value falls exactly on the max value
      yData(binCount - 1) += 1
    } else if (deltaDouble > max) {
      /* this data point is bigger than max */
    } else {
      val bin = ((deltaDouble - min) / binSize).toInt % binCount
      yData(bin) += 1
    }
  })
}

