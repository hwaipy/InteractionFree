package com.interactionfree.instrument.tdc

import java.io.FileInputStream
import java.util.Properties
import java.util.concurrent.Executors
import java.util.concurrent.atomic.{AtomicBoolean, AtomicLong, AtomicReference}
import scala.concurrent.duration.Duration
import scala.collection.mutable
import scala.io.Source
import com.interactionfree.IFWorker
import scala.concurrent.{Await, ExecutionContext, Future}
import java.util.concurrent.LinkedBlockingQueue
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.nio.file.Files
import java.nio.file.Paths
import java.io.RandomAccessFile

object TDCServer extends App {
  val properties = new Properties()
  val propertiesIn = new FileInputStream("config.properties")
  properties.load(propertiesIn)
  propertiesIn.close()

  val IFServerAddress = properties.getOrDefault("IFServer.Address", "tcp://172.16.60.200:224").toString
  val IFServerServiceName = properties.getOrDefault("IFServer.ServiceName", "TDCServer_Test").toString
  val IFServerAdapterAddress = properties.getOrDefault("TDCAdapter.Address", "tcp://127.0.0.1:224").toString
  val IFServerAdapterServiceName = properties.getOrDefault("TDCAdapter.ServiceName", "TDCServer").toString
  val storeCollection = properties.getOrDefault("StoreCollection", "TDCServerTestCollection").toString
  val processParallels = properties.getOrDefault("Parallels", "1").toString.toInt
  val isDebug = properties.getOrDefault("Debug", "false").toString.toBoolean
  val massiveStorePath = properties.getOrDefault("MassiveStorePath", "./").toString

  val process = new TDCServerProcessor()
  val worker = IFWorker(IFServerAddress, IFServerServiceName, process)
  val adapterWorker = if (IFServerAddress == IFServerAdapterAddress && IFServerServiceName == IFServerAdapterServiceName) worker else IFWorker(IFServerAdapterAddress, IFServerAdapterServiceName, process)

  if (isDebug) {
    process.setPostProcessStatus(true)
    process.turnOnAnalyser("Counter")
    process.turnOnAnalyser("MultiHistogram")
    process.turnOnAnalyser("TFQKDEncoding", Map("Period" -> 10000, "TriggerChannel" -> 0, "SignalChannel" -> 4, "RandomNumbers" -> Range(0, 129).toList))
    process.turnOnAnalyser("ExceptionMonitor", Map("SyncChannels" -> List(0)))
  }

  println(s"TDCServer started.")
  Source.stdin.getLines().filter(line => line.toLowerCase() == "q").next()
  println("Stoping TDCServer ...")
  worker.close()
  if (worker != adapterWorker) adapterWorker.close()
  process.stop()

  class TDCServerProcessor(threadCount: Int = 1) {
    private val channelCount = 16
    private val analysers = new mutable.HashMap[String, Analyser]()
    private val analysersMatcher = new mutable.HashMap[String, String]()
    private val postProcessOn = new AtomicBoolean(false)
    private val postProcessManagerExecutionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor())
    private val postProcessExecutionContext = ExecutionContext.fromExecutorService(Executors.newFixedThreadPool(threadCount))
    private val remoteStorageExecutionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor())
    private val remoteMassiveStorageExecutionContext = ExecutionContext.fromExecutorService(Executors.newSingleThreadExecutor())
    private val incomeDataBuffer = new mutable.ListBuffer[DataBlock]()
    private val incomeDataBufferMaxSize = 10e6
    private val previousStoreFuture = new AtomicReference[Future[Any]](null)
    private val running = new AtomicBoolean(true)
    private val delays = Range(0, channelCount).map(_ => 0L).toArray
    private val dataFormat = new SimpleDateFormat("yyyy-MM-dd")
    private val dataTimeFormat = new SimpleDateFormat("yyyy-MM-dd HH-mm-ss.SSS")

    def send(bytes: Array[Byte]): Unit = {
      println("get: " + bytes.size)
      val newDataBlock = DataBlock.deserialize(bytes, true)
      val bufferSize = incomeDataBuffer.map(db => db.binarySize()).sum
      if (bufferSize > incomeDataBufferMaxSize) newDataBlock.release()
      incomeDataBuffer += newDataBlock
    }

    private def performPostProcess(dataBlock: DataBlock) = {
      val overallBeginTime = System.nanoTime()
      val executionTimes = new mutable.HashMap[String, Double]()
      val result = new mutable.HashMap[String, Any]()
      dataBlock.unpack()
      val syncedDataBlock = dataBlock.synced(delays.toList, Map("Method" -> "PeriodSignal", "SyncChannel" -> "0", "Period" -> "40000000"))
      val massiveStoreFuture = Future[Any] {
        try {
          val date = dataFormat.format(dataBlock.creationTime)
          val dateTime = dataTimeFormat.format(dataBlock.creationTime)
          val path = Paths.get(massiveStorePath, date)
          if (Files.notExists(path)) Files.createDirectories(path)
          val raf = new RandomAccessFile(path.resolve(dateTime).toFile(), "rw")
          raf.write(syncedDataBlock.serialize())
          raf.close()
          executionTimes("Massive Store Time") = (System.nanoTime() - overallBeginTime) / 1e9
        } catch {
          case e: Throwable => println("[2]" + e)
        }
      }(remoteMassiveStorageExecutionContext)
      executionTimes("Unpack Time") = (System.nanoTime() - overallBeginTime) / 1e9
      analysers.toList
        .map(e => {
          (
            e._1,
            Future[Option[Map[String, Any]]] {
              val beginTime = System.nanoTime()
              val db = analysersMatcher(e._1) match {
                case "Original" => dataBlock
                case "Synced"   => syncedDataBlock
                case _          => throw new IllegalArgumentException("Unsupported DataBlock Mode.")
              }
              val r = e._2.dataIncome(db)
              val endTime = System.nanoTime()
              executionTimes(e._1) = (endTime - beginTime) / 1e9
              r
            }(postProcessExecutionContext)
          )
        })
        .map(f => (f._1, Await.result[Option[Map[String, Any]]](f._2, Duration.Inf)))
        .filter(e => e._2.isDefined)
        .foreach(e => {
          result(e._1) = e._2.get
        })
      val waitForPreviousFutureBeginTime = System.nanoTime()
      if (previousStoreFuture.get != null) Await.result(previousStoreFuture.get, Duration.Inf)
      Await.result(massiveStoreFuture, Duration.Inf)
      val waitForPreviousFutureEndTime = System.nanoTime()
      executionTimes("Wait Previous Storage Future") = (waitForPreviousFutureEndTime - waitForPreviousFutureBeginTime) / 1e9
      val overallTime = System.nanoTime() - overallBeginTime
      executionTimes("Overall") = overallTime / 1e9
      result("ExecutionTimes") = executionTimes

      previousStoreFuture set Future[Any] {
        println("Store")
        try {
          worker.Storage.append(storeCollection, result, fetchTime = dataBlock.creationTime)
        } catch {
          case e: Throwable => println("[1]" + e)
        }
      }(remoteStorageExecutionContext)

      // val subTimes = (executionTimes).toList
      // val subTimeString = subTimes.map(z => (z._2, z._1)).sorted.reverse.map(z => f"${z._2}: ${z._1}%.3f s").mkString(", ")

//     println(f"DataBlock [${dataBlock.content.map(_.size).sum / 1e6}%.3f MB] parsed in ${overallTime / 1e9} s. ${subTimeString}")
    }

    Future[Any] {
      while (running.get) {
        try {
          incomeDataBuffer.size match {
            case 0 => Thread.sleep(50)
            case _ => {
              val next = incomeDataBuffer.remove(0)
              if (next.isReleased) println("A released DataBlock.")
              else {
                if (postProcessOn.get) {
                  performPostProcess(next)
                }
              }
            }
          }
        } catch {
          case t: Throwable => t.printStackTrace()
        }
      }
    }(postProcessManagerExecutionContext)

    analysers("Counter") = new CounterAnalyser()
    analysersMatcher("Counter") = "Original"
    analysers("MultiHistogram") = new MultiHistogramAnalyser(channelCount)
    analysersMatcher("MultiHistogram") = "Synced"
    analysers("TFQKDEncoding") = new EncodingAnalyser(channelCount, 129)
    analysersMatcher("TFQKDEncoding") = "Synced"
    analysers("ExceptionMonitor") = new ExceptionMonitorAnalyser(16)
    analysersMatcher("ExceptionMonitor") = "Original"

    def stop() = {
      running set false
      // server.stop()
      postProcessManagerExecutionContext.shutdown()
      postProcessExecutionContext.shutdown()
      remoteStorageExecutionContext.shutdown()
      remoteMassiveStorageExecutionContext.shutdown()
    }

    def turnOnAnalyser(name: String, paras: Map[String, Any] = Map()) =
      analysers.get(name) match {
        case Some(analyser) => analyser.turnOn(paras)
        case None           => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
      }

    def configureAnalyser(name: String, paras: Map[String, Any]) =
      analysers.get(name) match {
        case Some(analyser) => analyser.configure(paras)
        case None           => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
      }

    def getAnalyserConfiguration(name: String) = {
      analysers.get(name) match {
        case Some(analyser) => analyser.getConfigurations
        case None           => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
      }
    }

    def turnOffAnalyser(name: String) =
      analysers.get(name) match {
        case Some(analyser) => analyser.turnOff()
        case None           => throw new IllegalArgumentException(s"Analyser ${name} not exists.")
      }

    def turnOffAllAnalysers() = analysers.values.foreach(analyser => analyser.turnOff())

    def setDelays(delays: List[Long]) = {
      if (delays.size != this.delays.size) throw new IllegalArgumentException(s"Delays should has length of ${this.delays.size}.")
      delays.zipWithIndex.foreach(z => this.delays(z._2) = z._1)
    }

    def setDelay(channel: Int, delay: Long) = this.delays(channel) = delay

    def getDelays() = delays.toArray

    def getStoraCollectionName() = storeCollection

    def getChannelCount() = channelCount

//   def setLocalBufferPermenent(p: Boolean) = server.setLocalBufferPermenent(p)

//   def isLocalBufferPermenent(): Boolean = server.isLocalBufferPermenent()

    def setPostProcessStatus(p: Boolean) = postProcessOn set p

    def getPostProcessStatus() = postProcessOn.get()
  }
}
