package com.interactionfree.instrument.tdc

import java.util.concurrent.atomic.AtomicLong

import com.interactionfree.instrument.tdc.adapters.GroundTDCDataAdapter
import com.interactionfree.instrument.tdc.local.LocalTDCDataFeeder

import scala.collection.mutable
import scala.io.Source
import com.interactionfree.IFWorker
import com.interactionfree.instrument.tdc.application.{MDIQKDEncodingAnalyser, MDIQKDQBERAnalyser}

object GroundTDC extends App {
  println("This is GroundTDC.")
  //  val parameters = mutable.HashMap[String, String]()
  //  args.foreach(arg => {
  //    val splitted = arg.split("=", 2)
  //    if (splitted.size == 2) parameters.put(splitted(0), splitted(1))
  //  })

  //  val DEBUG = parameters.get("debug").getOrElse("false").toBoolean
  val LOCAL = true
  val dataSourceListeningPort = 20156

  val process = new TDCProcessService(dataSourceListeningPort)
  val worker = IFWorker("tcp://localhost:224", "GroundTDC", process)
  //  process.turnOnAnalyser("Counter")
  //  process.turnOnAnalyser("Histogram", Map("Sync" -> 0, "Signal" -> 1, "ViewStart" -> -100000, "ViewStop" -> 100000))
  //  process.turnOnAnalyser("MDIQKDEncoding", Map("RandomNumbers" -> List(0, 1, 2, 3, 4, 5, 6, 7, 8, 9), "Period" -> 10000, "SignalChannel" -> 1, "TriggerChannel" -> 0))
  //  process.turnOnAnalyser("MDIQKDQBER", Map())
  println(s"Ground TDC started on port ${dataSourceListeningPort}.")
  if (LOCAL) {
    println("LOCAL mode, starting LocalTDCDataFeeder.")
    LocalTDCDataFeeder.start(dataSourceListeningPort)
  }
  if (LOCAL) while (process.getFinishedConnection < 1) Thread.sleep(100) else Source.stdin.getLines.filter(line => line.toLowerCase == "q").next
  println("Stoping Ground TDC...")
  worker.close()
  process.stop
}

class TDCProcessService(port: Int) {
  private val channelCount = 16
  private val groundTDA = new GroundTDCDataAdapter(channelCount)
  private val dataTDA = new LongBufferToDataBlockListTDCDataAdapter(channelCount)
  private val server = new TDCProcessServer(channelCount, port, dataIncome, List(groundTDA, dataTDA))
  private val analysers = new mutable.HashMap[String, DataAnalyser]()
  //  private val pathRef = new AtomicReference[String]("/test/tdc/default.fs")
  //  private val storageRef = new AtomicReference[BlockingRemoteObject](null)
  analysers("Counter") = new CounterAnalyser(channelCount)
  //  analysers("Histogram") = new HistogramAnalyser(channelCount)
  analysers("MultiHistogram") = new MultiHistogramAnalyser(channelCount)
  analysers("CoincidenceHistogram") = new CoincidenceHistogramAnalyser(channelCount)
  analysers("MDIQKDEncoding") = new MDIQKDEncodingAnalyser(channelCount)
  analysers("MDIQKDQBER") = new MDIQKDQBERAnalyser(channelCount)

  protected[tdc] def getFinishedConnection = server.getFinishedConnections

  def stop() = server.stop

  private def dataIncome(data: Any) = {
    if (!data.isInstanceOf[List[_]]) throw new IllegalArgumentException(s"Wrong type: ${data.getClass}")
    data.asInstanceOf[List[DataBlock]].foreach(dataBlockIncome)
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
    //    result("Time") = System.currentTimeMillis()
    result("DataBlockCreationTime") = dataBlock.creationTime
    result("ExecutionTimes") = executionTimes
    if (GroundTDC.LOCAL) {
      try {
        GroundTDC.worker.Storage.append("TDCLocal", result)
      } catch {
        case e: Throwable => println(e)
      }
    }
  }

  //  def postInit(client: MessageClient) = {
  //    storageRef set client.blockingInvoker("StorageService")
  //    storageRef.get.FSFileInitialize("", pathRef.get)
  //  }

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
}