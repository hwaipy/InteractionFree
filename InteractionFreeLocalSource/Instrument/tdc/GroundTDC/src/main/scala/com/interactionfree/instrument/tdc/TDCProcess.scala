package com.interactionfree.instrument.tdc

import java.io.FileInputStream
import java.util.Properties
import java.util.concurrent.atomic.AtomicBoolean

import scala.jdk.CollectionConverters._
import com.interactionfree.instrument.tdc.adapters.GroundTDCDataAdapter
import com.interactionfree.instrument.tdc.local.LocalTDCDataFeeder

import scala.collection.mutable
import scala.io.Source
import com.interactionfree.IFWorker
import com.interactionfree.instrument.tdc.application.{MDIQKDEncodingAnalyser, MDIQKDQBERAnalyser}

object GroundTDC extends App {
  println("This is GroundTDC.")

  val properties = new Properties()
  val propertiesIn = new FileInputStream("config.properties")
  properties.load(propertiesIn)
  propertiesIn.close()

  //  val parameters = mutable.HashMap[String, String]()
  //  args.foreach(arg => {
  //    val splitted = arg.split("=", 2)
  //    if (splitted.size == 2) parameters.put(splitted(0), splitted(1))
  //  })

  val DEBUG = properties.getOrDefault("Sys.Debug", false).toString.toBoolean
  val LOCAL = properties.getOrDefault("Sys.Local", false).toString.toBoolean
  val dataSourceListeningPort = properties.getOrDefault("DataSource.Port", 20156).toString.toInt
  val storeCollection = properties.getOrDefault("Storage.Collection", "Default").toString
  val localStorePath = properties.getOrDefault("Storage.Local", "./local").toString
  val IFServerAddress = properties.getOrDefault("IFServer.Address", "tcp://127.0.0.1:224").toString
  val IFServerServiceName = properties.getOrDefault("IFServer.ServiceName", "GroundTDCService").toString
  val process = new TDCProcessService(dataSourceListeningPort, storeCollection, localStorePath)

  val worker = IFWorker(IFServerAddress, IFServerServiceName, process)
  println(s"Ground TDC started on port ${dataSourceListeningPort}.")
  if (LOCAL) {
    println("LOCAL mode, starting LocalTDCDataFeeder.")
    LocalTDCDataFeeder.start(dataSourceListeningPort)
  }
  Source.stdin.getLines().filter(line => line.toLowerCase() == "q").next()
  println("Stoping Ground TDC...")
  worker.close()
  process.stop()
}

class TDCProcessService(private val port: Int, private val storeCollection: String, private val localStorePath: String) {
  private val channelCount = 16
  private val groundTDA = new GroundTDCDataAdapter(channelCount)
  private val dataTDA = new LongBufferToDataBlockListTDCDataAdapter(channelCount)
  private val server = new TDCProcessServer(channelCount, port, dataIncome, List(groundTDA, dataTDA), localStorePath)
  private val analysers = new mutable.HashMap[String, DataAnalyser]()
  private val postProcessOn = new AtomicBoolean(false)
  analysers("Counter") = new CounterAnalyser(channelCount)
  analysers("MultiHistogram") = new MultiHistogramAnalyser(channelCount)
  analysers("CoincidenceHistogram") = new CoincidenceHistogramAnalyser(channelCount)
  analysers("MDIQKDEncoding") = new MDIQKDEncodingAnalyser(channelCount)
  analysers("MDIQKDQBER") = new MDIQKDQBERAnalyser(channelCount)

  protected[tdc] def getFinishedConnection = server.getFinishedConnections

  def stop() = server.stop()

  private def dataIncome(data: Any) = {
    if (!data.isInstanceOf[List[_]]) throw new IllegalArgumentException(s"Wrong type: ${data.getClass}")
    if(postProcessOn.get) data.asInstanceOf[List[DataBlock]].foreach(dataBlockIncome)
  }

  private def dataBlockIncome(dataBlock: DataBlock) = {
    val result = new mutable.HashMap[String, Any]()
    val executionTimes = new mutable.HashMap[String, Double]()
    analysers.toList.map(e => {
      val beginTime = System.nanoTime()
      val r = e._2.dataIncome(dataBlock)
      val endTime = System.nanoTime()
      executionTimes(e._1) = (endTime - beginTime) / 1e9
      (e._1, r)
    }).filter(e => e._2.isDefined).foreach(e => result(e._1) = e._2.get)
    result("ExecutionTimes") = executionTimes
    result("Delays") = dataTDA.delays
    try {
      GroundTDC.worker.Storage.append(storeCollection, result, fetchTime = dataBlock.creationTime)
    } catch {
      case e: Throwable => println("[1]" + e)
    }
  }

  def turnOnAnalyser(name: String, paras: Map[String, Any] = Map()) = analysers.get(name) match {
    case Some(analyser) => analyser.turnOn(paras)
    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  }

  def configureAnalyser(name: String, paras: Map[String, Any]) = analysers.get(name) match {
    case Some(analyser) => analyser.configure(paras)
    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  }

  def getAnalyserConfiguration(name: String) = analysers.get(name) match {
    case Some(analyser) => analyser.getConfiguration()
    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  }

  def turnOffAnalyser(name: String) = analysers.get(name) match {
    case Some(analyser) => analyser.turnOff()
    case None => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
  }

  def turnOffAllAnalysers() = analysers.values.foreach(analyser => analyser.turnOff())

  def setDelays(delays: List[Long]) = dataTDA.setDelays(delays)

  def setDelay(channel: Int, delay: Long) = dataTDA.setDelay(channel, delay)

  def getDelays() = dataTDA.getDelays()

  def getStoraCollectionName() = storeCollection

  def getChannelCount() = channelCount

  def setLocalBufferPermenent(p: Boolean) = server.setLocalBufferPermenent(p)

  def isLocalBufferPermenent() = server.isLocalBufferPermenent()

  def setPostProcessStatus(p: Boolean) = postProcessOn set p

  def getPostProcessStatus() = postProcessOn.get()
}