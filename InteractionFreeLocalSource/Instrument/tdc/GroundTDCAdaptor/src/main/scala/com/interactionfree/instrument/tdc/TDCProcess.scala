package com.interactionfree.instrument.tdc

import java.io.FileInputStream
import java.util.Properties
import java.util.concurrent.Executors
import java.util.concurrent.atomic.{AtomicBoolean, AtomicInteger, AtomicLong, AtomicReference}

import scala.concurrent.duration.Duration
import scala.jdk.CollectionConverters._
import com.interactionfree.instrument.tdc.adapters.GroundTDCDataAdapter

import scala.collection.mutable
import scala.io.Source
import com.interactionfree.IFWorker

import scala.concurrent.{Await, ExecutionContext, Future}

object GroundTDC extends App {
  println("This is GroundTDCAdaptor.")

  val properties = new Properties()
  val propertiesIn = new FileInputStream("config.properties")
  properties.load(propertiesIn)
  propertiesIn.close()

  if (properties.getProperty("BenchMarking") == "true") {
    BenchMarking.run()
  } else {
    val dataSourceListeningPort = properties.getOrDefault("DataSource.Port", 20156).toString.toInt
    val localStorePath = properties.getOrDefault("Storage.Local", "./local").toString
    val IFServerAddress = properties.getOrDefault("IFServer.Address", "tcp://127.0.0.1:224").toString
    val IFServerServiceName = properties.getOrDefault("IFServer.ServiceName", "GroundTDCService").toString
    val postProcessParallels = properties.getOrDefault("PostProcessParallels", "1").toString.toInt
    val process = new TDCProcessService(dataSourceListeningPort, localStorePath)

    val worker = IFWorker(IFServerAddress, IFServerServiceName, process)
    println(s"Ground TDC started on port $dataSourceListeningPort.")
    Source.stdin.getLines().filter(line => line.toLowerCase() == "q").next()
    println("Stoping Ground TDC...")
    worker.close()
    process.stop()
  }
}

class TDCProcessService(private val port: Int, private val localStorePath: String) {
  private val channelCount = 16
  private val groundTDA = new GroundTDCDataAdapter(channelCount)
  private val dataTDA = new LongBufferToDataBlockListTDCDataAdapter(channelCount)
  private val server = new TDCProcessServer(channelCount, port, dataIncome, List(groundTDA, dataTDA), localStorePath)
  private val running = new AtomicBoolean(true)
  private val bufferSize = 10 * 1000000

  def stop() = {
    running set false
    server.stop()
  }

  private def dataIncome(data: Any) = {
    if (!data.isInstanceOf[List[_]]) throw new IllegalArgumentException(s"Wrong type: ${data.getClass}")
    data.asInstanceOf[List[DataBlock]].foreach(dataBlock => dataBlockIncome(dataBlock))
  }

  private val dataBlockQueue = new collection.mutable.ListBuffer[DataBlock]

  private def dataBlockIncome(dataBlock: DataBlock) = {
    this.synchronized {
      println("get a dB")
      dataBlockQueue += dataBlock
      while (bufferStatus._3 >= bufferSize) dataBlockQueue.filter(!_.isReleased).head.release()
    }
  }

  // DataBlock count, released DataBlock count, valid size.
  def bufferStatus = (dataBlockQueue.size, dataBlockQueue.filter(_.isReleased).size, dataBlockQueue.filter(!_.isReleased).map(_.sizes.sum).sum)

  Future[Any] {
    while (running.get) {
      this.synchronized {
        dataBlockQueue.size match {
          case 0 => None
          case _ => Some(dataBlockQueue.remove(0))
        }
      } match {
        case Some(next) => println("send a dB")
        case None => Thread.sleep(100)
      }
    }
  }(ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor((r) => {
    val t = new Thread(r)
    t.setDaemon(true)
    t
  })))


  //  def turnOnAnalyser(name: String, paras: Map[String, Any] = Map()) = analysers.get(name) match {
  //    case Some(analyser) => analyser.turnOn(paras)
  //    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  //  }
  //
  //  def configureAnalyser(name: String, paras: Map[String, Any]) = analysers.get(name) match {
  //    case Some(analyser) => analyser.configure(paras)
  //    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  //  }
  //
  //  def getAnalyserConfiguration(name: String) = analysers.get(name) match {
  //    case Some(analyser) => analyser.getConfiguration()
  //    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  //  }
  //
  //  def turnOffAnalyser(name: String) = analysers.get(name) match {
  //    case Some(analyser) => analyser.turnOff()
  //    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  //  }
  //
  //  def turnOffAllAnalysers() = analysers.values.foreach(analyser => analyser.turnOff())
  //
  //  def setDelays(delays: List[Long]) = dataTDA.setDelays(delays)
  //
  //  def setDelay(channel: Int, delay: Long) = dataTDA.setDelay(channel, delay)
  //
  //  def getDelays() = dataTDA.getDelays()
  //
  //  def getStoraCollectionName() = storeCollection
  //
  //  def getChannelCount() = channelCount
  //
  //  def setLocalBufferPermenent(p: Boolean) = server.setLocalBufferPermenent(p)
  //
  //  def isLocalBufferPermenent(): Boolean = server.isLocalBufferPermenent()
  //
  //  def setPostProcessStatus(p: Boolean) = postProcessOn set p
  //
  //  def getPostProcessStatus() = postProcessOn.get()
}

object BenchMarking {
  def run(): Unit = {
    println("******** Start BenchMarking ********")
    println("Period List")
    doBenchMarking("\t10000", Map(0 -> List("Period", 10000)))
    doBenchMarking("\t100000", Map(0 -> List("Period", 100000)))
    doBenchMarking("\t1000000", Map(0 -> List("Period", 1000000)))
    doBenchMarking("\t4000000", Map(0 -> List("Period", 4000000)))
    println("Random List")
    doBenchMarking("\t10000", Map(0 -> List("Random", 10000)))
    doBenchMarking("\t100000", Map(0 -> List("Random", 100000)))
    doBenchMarking("\t1000000", Map(0 -> List("Random", 1000000)))
    doBenchMarking("\t4000000", Map(0 -> List("Random", 4000000)))
    println("Mixed")
    doBenchMarking("\t10000", Map(0 -> List("Period", 1000), 1 -> List("Random", 4000), 5 -> List("Random", 5000), 10 -> List("Period", 10), 12 -> List("Random", 1)))
    doBenchMarking("\t100000", Map(0 -> List("Period", 10000), 1 -> List("Random", 40000), 5 -> List("Random", 50000), 10 -> List("Period", 10), 12 -> List("Random", 1)))
    doBenchMarking("\t1000000", Map(0 -> List("Period", 100000), 1 -> List("Random", 400000), 5 -> List("Random", 500000), 10 -> List("Period", 10), 12 -> List("Random", 1)))
    doBenchMarking("\t4000000", Map(0 -> List("Period", 400000), 1 -> List("Random", 1600000), 5 -> List("Random", 2000000), 10 -> List("Period", 10), 12 -> List("Random", 1)))
  }

  def doBenchMarking(condition: String, dataConfig: Map[Int, List[Any]]) = {
    val testDataBlock = DataBlock.generate(Map("CreationTime" -> 100, "DataTimeBegin" -> 10, "DataTimeEnd" -> 1000000000010L), dataConfig)
    val consumingSerialization = doBenchMarkingOpertion(() => testDataBlock.serialize())
    val data = testDataBlock.serialize()
    val infoRate = data.length.toDouble / testDataBlock.getContent.map(_.length).sum
    val consumingDeserialization = doBenchMarkingOpertion(() => DataBlock.deserialize(data))
    println(f"$condition\t\t\t\t\t${infoRate}%.2f\t\t\t${consumingSerialization * 1000}%.1f ms\t\t\t${consumingDeserialization * 1000}%.1f ms")
  }

  def doBenchMarkingOpertion(operation: () => Unit) = {
    val stop = System.nanoTime() + 1000000000
    val count = new AtomicInteger(0)
    while (System.nanoTime() < stop) {
      operation()
      count.incrementAndGet()
    }
    (1e9 + System.nanoTime() - stop) / 1e9 / count.get
  }
}