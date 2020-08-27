package com.interactionfree.instrument.tdc

import java.io.FileInputStream
import java.util.Properties
import java.util.concurrent.Executors
import java.util.concurrent.atomic.{AtomicBoolean, AtomicLong, AtomicReference}

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

  val dataSourceListeningPort = properties.getOrDefault("DataSource.Port", 20156).toString.toInt
  val localStorePath = properties.getOrDefault("Storage.Local", "./local").toString
  val IFServerAddress = properties.getOrDefault("IFServer.Address", "tcp://127.0.0.1:224").toString
  val IFServerServiceName = properties.getOrDefault("IFServer.ServiceName", "GroundTDCService").toString
  val postProcessParallels = properties.getOrDefault("PostProcessParallels", "1").toString.toInt
  val process = new TDCProcessService(dataSourceListeningPort, localStorePath)

  val worker = IFWorker(IFServerAddress, IFServerServiceName, process)
  println(s"Ground TDC started on port ${dataSourceListeningPort}.")
  Source.stdin.getLines().filter(line => line.toLowerCase() == "q").next()
  //  Thread.sleep(5000)
  println("Stoping Ground TDC...")
  worker.close()
  process.stop()
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
