package com.interactionfree.instrument.tdc

import com.interactionfree.IFException
import com.interactionfree.NumberTypeConversions._

import scala.collection.mutable
import scala.collection.mutable.ArrayBuffer

abstract class Analyser {
  private var on = false
  private val configuration = new mutable.HashMap[String, Tuple2[Any, Any => Boolean]]()

  def turnOn(paras: Map[String, Any] = Map()): Unit = {
    on = true
    configure(paras)
  }

  def turnOff(): Unit = on = false

  def isTurnedOn: Boolean = on

  def dataIncome(dataBlock: DataBlock): Option[Map[String, Any]] = if (on) Some(analysis(dataBlock) ++ Map("Configuration" -> configuration.map(e => (e._1, e._2._1)).toMap)) else None

  protected def analysis(dataBlock: DataBlock): Map[String, Any]

  def configure(paras: Map[String, Any]): Unit = paras.foreach(e => configuration.get(e._1) match {
    case None => throw new IFException(s"[${e._1}] is not a valid configuration key.")
    case Some(vv) => if (vv._2(e._2)) configuration(e._1) = (e._2, vv._2) else throw new IFException(s"Configuration ${e._1} -> ${e._2} is not valid.")
  })

  protected def setConfiguration(key: String, defaultValue: Any, validator: Any => Boolean = a => true): Unit = configuration(key) = (defaultValue, validator)

  def getConfigurations: Map[String, Any] = configuration.toMap

  def getConfiguration(key: String) = configuration.get(key) match {
    case None => throw new IFException(s"[$key] is not a valid configuration key.")
    case Some(vv) => vv._1
  }
}

object Validator {
  private def wrap(validator: Any => Boolean) = (any: Any) =>
    try {
      validator(any)
    } catch {
      case e: Throwable => false
    }

  def int(min: Int = Int.MinValue, max: Int = Int.MaxValue) = wrap(value => anyToInt(value) >= min && anyToInt(value) <= max)

  def double(min: Double = Double.NegativeInfinity, max: Double = Double.PositiveInfinity) = wrap(value => anyToDouble(value) >= min && anyToDouble(value) <= max)
}

class CounterAnalyser extends Analyser {

  override protected def analysis(dataBlock: DataBlock): Map[String, Int] = Range(0, dataBlock.content.size).map(_.toString()).zip(dataBlock.content.map(list => list.length)).toMap
}

class MultiHistogramAnalyser(channelCount: Int) extends Analyser {
  setConfiguration("Sync", 0, Validator.int(0, channelCount - 1))
  setConfiguration("Signals", 0, value => value.asInstanceOf[List[Int]].forall(c => c >= 0 && c < channelCount))
  setConfiguration("ViewStart", -100000, Validator.double())
  setConfiguration("ViewStop", 100000, Validator.double())
  setConfiguration("BinCount", 1000, Validator.int(1, 10000))
  setConfiguration("Divide", 1, Validator.int(min = 1))

  override protected def analysis(dataBlock: DataBlock) = {
    val syncChannel: Int = getConfiguration("Sync")
    val signalChannels = getConfiguration("Signals").asInstanceOf[List[Int]]
    val viewStart: Long = getConfiguration("ViewStart")
    val viewStop: Long = getConfiguration("ViewStop")
    val binCount: Int = getConfiguration("BinCount")
    val divide: Int = getConfiguration("Divide")
    val tList = dataBlock.getContent(syncChannel)
    val viewFrom = viewStart
    val viewTo = viewStop
    val histograms = signalChannels.map(signalChannel => {
      val deltas = new ArrayBuffer[Long]()
      val sList = dataBlock.getContent(signalChannel)
      if (tList.size > 0 && sList.size > 0) {
        var preStartT = 0
        val lengthT = tList.size
        var sp = 0
        while (sp < sList.size) {
          val s = sList(sp)
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
          sp += 1
        }
      }
      new Histogram(deltas.toArray, binCount, viewFrom, viewTo, divide).yData.toList
    })
    Map[String, Any]("Histograms" -> histograms)
  }
}

//class CoincidenceHistogramAnalyser(channelCount: Int) extends DataAnalyser {
//  configuration("ChannelA") = 0
//  configuration("ChannelB") = 1
//  configuration("ViewStart") = -100000
//  configuration("ViewStop") = 100000
//  configuration("BinCount") = 1000
//
//  override def configure(key: String, value: Any) = {
//    key match {
//      case "ChannelA" => {
//        val sc: Int = value
//        sc >= 0 && sc < channelCount
//      }
//      case "ChannelB" => {
//        val sc: Int = value
//        sc >= 0 && sc < channelCount
//      }
//      case "ViewStart" => true
//      case "ViewStop" => true
//      case "BinCount" => {
//        val sc: Int = value
//        sc > 0 && sc < 2000
//      }
//      case _ => false
//    }
//  }
//
//  override protected def analysis(dataBlock: DataBlock) = {
//    val deltas = new ArrayBuffer[Long]()
//    val syncChannel: Int = configuration("ChannelA")
//    val signalChannel: Int = configuration("ChannelB")
//    val viewStart: Long = configuration("ViewStart")
//    val viewStop: Long = configuration("ViewStop")
//    val binCount: Int = configuration("BinCount")
//    val tList = dataBlock.content(syncChannel)
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
//    val histo = new Histogram(deltas.toArray, binCount, viewFrom, viewTo, 1)
//    Map[String, Any]("Histogram" -> histo.yData.toList)
//  }
//}

class Histogram(deltas: Array[Long], binCount: Int, viewFrom: Long, viewTo: Long, divide: Int) {
  val min = viewFrom.toDouble
  val max = viewTo.toDouble
  val binSize = (max - min) / binCount / divide
  val xData = Range(0, binCount).map(i => (i * binSize + min) + binSize / 2).toArray
  val yData = new Array[Int](binCount)
  initData()

  private def initData(): Unit = {
    var dp = 0
    while (dp < deltas.size) {
      val delta = deltas(dp)
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
      dp += 1
    }
  }
}

