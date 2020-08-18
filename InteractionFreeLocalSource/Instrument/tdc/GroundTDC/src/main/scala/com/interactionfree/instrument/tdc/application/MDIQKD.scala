package com.interactionfree.instrument.tdc.application

import java.util.concurrent.Executors
import java.util.concurrent.atomic.{AtomicLong, AtomicReference}

import com.interactionfree.instrument.tdc.{DataAnalyser, DataBlock, Histogram}
import com.interactionfree.NumberTypeConversions._
import com.interactionfree.instrument.tdc.local.BenchMarking

import scala.collection.mutable
import scala.collection.mutable.{ArrayBuffer, ListBuffer}
import scala.concurrent.duration.Duration
import scala.concurrent.{Await, ExecutionContext, Future}

class MDIQKDEncodingAnalyser(channelCount: Int) extends DataAnalyser {
  configuration("RandomNumbers") = List(1)
  configuration("Period") = 10000.0
  configuration("TriggerChannel") = 0
  configuration("SignalChannel") = 1
  configuration("TimeAliceChannel") = 4
  configuration("TimeBobChannel") = 5
  configuration("BinCount") = 100

  override def configure(key: String, value: Any) = key match {
    case "RandomNumbers" => value.asInstanceOf[List[Int]] != null
    case "Period" => {
      val sc: Double = value
      sc > 0
    }
    case "SignalChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "TriggerChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "TimeAliceChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "TimeBobChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "BinCount" => {
      val sc: Int = value
      sc > 0 && sc < 2000
    }
    case _ => false
  }

  override protected def analysis(dataBlock: DataBlock) = {
    val randomNumbers = configuration("RandomNumbers").asInstanceOf[List[Int]].map(r => new RandomNumber(r)).toArray
    val period: Double = configuration("Period")
    val triggerChannel: Int = configuration("TriggerChannel")
    val timeAliceChannel: Int = configuration("TimeAliceChannel")
    val timeBobChannel: Int = configuration("TimeBobChannel")
    val signalChannel: Int = configuration("SignalChannel")
    val binCount: Int = configuration("BinCount")
    val map = mutable.HashMap[String, Any]()

    val signalList = dataBlock.content(signalChannel)
    val triggerList = dataBlock.content(triggerChannel)
    val timeAliceList = dataBlock.content(timeAliceChannel)
    val timeBobList = dataBlock.content(timeBobChannel)
    val meta = this.meta(signalList, triggerList, period, randomNumbers)
    RandomNumber.ALL_RANDOM_NUMBERS.foreach(rn => {
      val validMeta = meta.filter(z => z._1 == rn)
      val histoPulse = new Histogram(validMeta.map(_._2), binCount, 0, period.toLong, 1)
      map.put(s"Histogram with RandomNumber[${rn.RN}]", histoPulse.yData.toList)
      map.put(s"Pulse Count of RandomNumber[${rn.RN}]", randomNumbers.map(_.RN).count(_ == rn.RN))
    })
    val metaTimeAlice = this.meta(timeAliceList, triggerList, period, randomNumbers)
    val histoTimeAlice = new Histogram(metaTimeAlice.map(_._2), binCount, 0, period.toLong, 1)
    map.put(s"Histogram Alice Time", histoTimeAlice.yData.toList)
    val metaTimeBob = this.meta(timeBobList, triggerList, period, randomNumbers)
    val histoTimeBob = new Histogram(metaTimeBob.map(_._2), binCount, 0, period.toLong, 1)
    map.put(s"Histogram Bob Time", histoTimeBob.yData.toList)
    map.toMap
  }

  private def meta(signalList: Array[Long], triggerList: Array[Long], period: Double, randomNumbers: Array[RandomNumber]) = {
    val triggerIterator = triggerList.iterator
    val currentTriggerRef = new AtomicLong(if (triggerIterator.hasNext) triggerIterator.next() else 0)
    val nextTriggerRef = new AtomicLong(if (triggerIterator.hasNext) triggerIterator.next() else Long.MaxValue)
    signalList.map(time => {
      while (time >= nextTriggerRef.get) {
        currentTriggerRef set nextTriggerRef.get
        nextTriggerRef.set(if (triggerIterator.hasNext) triggerIterator.next() else Long.MaxValue)
      }
      val pulseIndex = ((time - currentTriggerRef.get) / period).toLong
      val randomNumberIndex = (pulseIndex % randomNumbers.size).toInt
      val randomNumber = randomNumbers(if (randomNumberIndex >= 0) randomNumberIndex else randomNumberIndex + randomNumbers.size)
      val delta = (time - currentTriggerRef.get - period * pulseIndex).toLong
      (randomNumber, delta)
    })
  }
}

class MDIQKDQBERAnalyser(channelCount: Int) extends DataAnalyser {
  configuration("AliceRandomNumbers") = Range(0, 10000).map(_ => 0).toList
  configuration("BobRandomNumbers") = Range(0, 10000).map(_ => 0).toList
  configuration("Period") = 10000.0
  configuration("Delay") = 3000.0
  configuration("PulseDiff") = 3000.0
  configuration("Gate") = 2000.0
  configuration("TriggerChannel") = 0
  configuration("Channel 1") = 1
  configuration("Channel 2") = 3
  configuration("Channel Monitor Alice") = 4
  configuration("Channel Monitor Bob") = 5
  configuration("QBERSectionCount") = 1000
  configuration("HOMSidePulses") = List(-100, -99, -98, 98, 99, 100)
  configuration("ChannelMonitorSyncChannel") = 2
  val executionContext = ExecutionContext.fromExecutorService(Executors.newFixedThreadPool(4))
  private val benchMarker = ListBuffer[BenchMarking]()

  override def configure(key: String, value: Any) = key match {
    case "AliceRandomNumbers" => value.asInstanceOf[List[Int]] != null
    case "BobRandomNumbers" => value.asInstanceOf[List[Int]] != null
    case "HOMSidePulses" => value.asInstanceOf[List[Int]] != null
    case "Period" => {
      val sc: Double = value
      sc > 0
    }
    case "Delay" => {
      val sc: Double = value
      true
    }
    case "Gate" => {
      val sc: Double = value
      true
    }
    case "PulseDiff" => {
      val sc: Double = value
      true
    }
    case "Channel 1" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "Channel 2" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "Channel Monitor Alice" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "Channel Monitor Bob" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "TriggerChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "QBERSectionCount" => {
      val sc: Int = value
      sc > 0
    }
    case "ChannelMonitorSyncChannel" => {
      val sc: Int = value
      sc >= 0 && sc < channelCount
    }
    case "BenchMarking" => {
      benchMarker addOne value.asInstanceOf[BenchMarking]
      false
    }
    case _ => false
  }

  override protected def analysis(dataBlock: DataBlock) = {
    benchMarker.foreach(b => b.tag("begin analysis"))

    val map = mutable.HashMap[String, Any]()
    val randomNumbersAlice = configuration("AliceRandomNumbers").asInstanceOf[List[Int]].map(r => new RandomNumber(r)).toArray
    val randomNumbersBob = configuration("BobRandomNumbers").asInstanceOf[List[Int]].map(r => new RandomNumber(r)).toArray
    val period: Double = configuration("Period")
    val delay: Double = configuration("Delay")
    val pulseDiff: Double = configuration("PulseDiff")
    val gate: Double = configuration("Gate")
    val triggerChannel: Int = configuration("TriggerChannel")
    val channel1: Int = configuration("Channel 1")
    val channel2: Int = configuration("Channel 2")
    val channelMonitorAlice: Int = configuration("Channel Monitor Alice")
    val channelMonitorBob: Int = configuration("Channel Monitor Bob")
    val qberSectionCount: Int = configuration("QBERSectionCount")
    val HOMSidePulses = configuration("HOMSidePulses").asInstanceOf[List[Int]]
    val channelMonitorSyncChannel: Int = configuration("ChannelMonitorSyncChannel")

    val triggerList = dataBlock.content(triggerChannel)
    val signalList1 = dataBlock.content(channel1)
    val signalList2 = dataBlock.content(channel2)
    val monitorListAlice = dataBlock.content(channelMonitorAlice)
    val monitorListBob = dataBlock.content(channelMonitorBob)

    // bellow consider parallels
    benchMarker.foreach(b => b.tag("config done"))

    val item1sFuture = Future[Tuple2[Array[Tuple4[Long, Long, Int, Long]], Array[Tuple4[Long, Long, Int, Long]]]] {
      val items = analysisSingleChannel(triggerList, signalList1, period, delay, gate, pulseDiff, randomNumbersAlice.size)
      (items, items.filter(_._3 >= 0))
    }(executionContext)
    val item2sFuture = Future[Tuple2[Array[Tuple4[Long, Long, Int, Long]], Array[Tuple4[Long, Long, Int, Long]]]] {
      val items = analysisSingleChannel(triggerList, signalList2, period, delay, gate, pulseDiff, randomNumbersBob.size)
      (items, items.filter(_._3 >= 0))
    }(executionContext)
    val item1sFutureResult = Await.result(item1sFuture, Duration.Inf)
    val item2sFutureResult = Await.result(item2sFuture, Duration.Inf)
    val item1s = item1sFutureResult._1
    val validItem1s = item1sFutureResult._2
    val item2s = item2sFutureResult._1
    val validItem2s = item2sFutureResult._2
    benchMarker.foreach(b => b.tag("valid items's"))

    def generateCoincidences(iterator1: Iterator[Tuple4[Long, Long, Int, Long]], iterator2: Iterator[Tuple4[Long, Long, Int, Long]]) = {
      val item1Ref = new AtomicReference[Tuple4[Long, Long, Int, Long]]()
      val item2Ref = new AtomicReference[Tuple4[Long, Long, Int, Long]]()

      def fillRef = {
        if (item1Ref.get == null && iterator1.hasNext) item1Ref set iterator1.next()
        if (item2Ref.get == null && iterator2.hasNext) item2Ref set iterator2.next()
        item1Ref.get != null && item2Ref.get != null
      }

      val resultBuffer = new ArrayBuffer[Coincidence]()
      while (fillRef) {
        val item1 = item1Ref.get
        val item2 = item2Ref.get
        if (item1._1 > item2._1) item2Ref set null
        else if (item1._1 < item2._1) item1Ref set null
        else if (item1._2 > item2._2) item2Ref set null
        else if (item1._2 < item2._2) item1Ref set null
        else {
          resultBuffer += new Coincidence(item1._3, item2._3, randomNumbersAlice(item1._2 % randomNumbersAlice.size), randomNumbersBob(item1._2 % randomNumbersBob.size), item1._4, item1._1, item1._2)
          item1Ref set null
          item2Ref set null
        }
      }
      resultBuffer.toList
    }

    def generateCoincidencesInFuture(delta: Int) = {
      Future[List[Coincidence]] {
        val i2it = if (delta == 0) validItem2s.iterator else validItem2s.map(i => (i._1 + delta, i._2, i._3, i._4)).iterator
        generateCoincidences(validItem1s.iterator, i2it)
      }(executionContext)
    }

    val coincidencesFuture = generateCoincidencesInFuture(0)
    val sideCoincidencesFutures = HOMSidePulses.map(delta => generateCoincidencesInFuture(delta))

//    val coincidences = generateCoincidences(validItem1s.iterator, validItem2s.iterator)
    val coincidences = Await.result(coincidencesFuture, Duration.Inf)
    val validCoincidences = coincidences.filter(_.valid)
    val basisMatchedCoincidences = coincidences.filter(_.basisMatched)
    benchMarker.foreach(b => b.tag("coincidences"))

    val basisStrings = List("O", "X", "Y", "Z")
    val qberSections = Range(0, qberSectionCount).toArray.map(i => new Array[Int](4 * 4 * 2)) // 4 basis * 4 basis * (right/wrong)
    Range(0, 4).foreach(basisAlice => Range(0, 4).foreach(basisBob => {
      val coincidences = validCoincidences.filter(c => c.randomNumberAlice.intensity == basisAlice && c.randomNumberBob.intensity == basisBob)
      map.put(s"${basisStrings(basisAlice)}-${basisStrings(basisBob)}, Correct", coincidences.filter(_.isCorrect).size)
      map.put(s"${basisStrings(basisAlice)}-${basisStrings(basisBob)}, Wrong", coincidences.filterNot(_.isCorrect).size)
    }))
    validCoincidences.foreach(c => {
      val sectionIndex = ((c.triggerTime - dataBlock.dataTimeBegin).toDouble / (dataBlock.dataTimeEnd - dataBlock.dataTimeBegin) * qberSectionCount).toInt
      val category = (c.randomNumberAlice.intensity * 4 + c.randomNumberBob.intensity) * 2 + (if (c.isCorrect) 0 else 1)
      if (sectionIndex >= 0 && sectionIndex < qberSections.size) qberSections(sectionIndex)(category) += 1
    })
    map.put(s"QBER Sections", qberSections)
    map.put(s"QBER Sections Detail", s"1000*32 Array. 1000 for 1000 sections. 32 for (Alice[O,X,Y,Z] * 4 + Bob[O,X,Y,Z]) * 2 + (0 for Correct and 1 for Wrong)")
    benchMarker.foreach(b => b.tag("QBER sections"))

    val sideCoincidences = sideCoincidencesFutures.map(f => Await.result(f, Duration.Inf).filter(c => (c.r1 == 0) && (c.r2 == 0)))
    benchMarker.foreach(b => b.tag("side coincidences"))

    val ccsXX0Coincidences = basisMatchedCoincidences.filter(c => c.randomNumberAlice.isX && c.randomNumberBob.isX).filter(c => (c.r1 == 0) && (c.r2 == 0))
//    val ccsXXOtherCoincidences = HOMSidePulses.map(delta => generateCoincidences(validItem1s.iterator, validItem2s.map(i => (i._1 + delta, i._2, i._3, i._4)).iterator)
//      .filter(_.basisMatched).filter(c => c.randomNumberAlice.isX && c.randomNumberBob.isX).filter(c => (c.r1 == 0) && (c.r2 == 0)))
    val ccsXXOtherCoincidences = sideCoincidences.map(sideCs => sideCs.filter(c => c.randomNumberAlice.isX && c.randomNumberBob.isX))
    val ccsXX0 = ccsXX0Coincidences.size
    val ccsXXOther = ccsXXOtherCoincidences.map(_.size)
    map.put("HOM X0-X0", List(ccsXX0, ccsXXOther.sum.toDouble / ccsXXOther.size))

    val ccsYY0Coincidences = basisMatchedCoincidences.filter(c => c.randomNumberAlice.isY && c.randomNumberBob.isY).filter(c => (c.r1 == 0) && (c.r2 == 0))
//    val ccsYYOtherCoincidences = HOMSidePulses.map(delta => generateCoincidences(validItem1s.iterator, validItem2s.map(i => (i._1 + delta, i._2, i._3, i._4)).iterator)
//      .filter(_.basisMatched).filter(c => c.randomNumberAlice.isY && c.randomNumberBob.isY).filter(c => (c.r1 == 0) && (c.r2 == 0)))
    val ccsYYOtherCoincidences = sideCoincidences.map(sideCs => sideCs.filter(c => c.randomNumberAlice.isY && c.randomNumberBob.isY))
    val ccsYY0 = ccsYY0Coincidences.size
    val ccsYYOther = ccsYYOtherCoincidences.map(_.size)
    map.put("HOM Y0-Y0", List(ccsYY0, ccsYYOther.sum.toDouble / ccsYYOther.size))

    val ccsAll0Coincidences = coincidences.filter(c => (c.r1 == 0) && (c.r2 == 0))
//    val ccsAllOtherCoincidences = HOMSidePulses.map(delta => generateCoincidences(validItem1s.iterator, validItem2s.map(i => (i._1 + delta, i._2, i._3, i._4)).iterator).filter(c => (c.r1 == 0) && (c.r2 == 0)))
    val ccsAllOtherCoincidences = sideCoincidences

    val ccsAll0 = ccsAll0Coincidences.size
    val ccsAllOther = ccsAllOtherCoincidences.map(_.size)
    map.put("HOM, All0-All0", List(ccsAll0, ccsAllOther.sum.toDouble / ccsAllOther.size))

    def statisticCoincidenceSection(cll: List[List[Coincidence]]) = {
      val sections = new Array[Int](qberSectionCount)
      cll.foreach(cl => cl.foreach(c => {
        val sectionIndex = ((c.triggerTime - dataBlock.dataTimeBegin).toDouble / (dataBlock.dataTimeEnd - dataBlock.dataTimeBegin) * qberSectionCount).toInt
        if (sectionIndex >= 0 && sectionIndex < qberSections.size) sections(sectionIndex) += 1
      }))
      sections.map(c => c.toDouble / cll.size)
    }

    val homSections = Array(List(ccsXX0Coincidences), ccsXXOtherCoincidences, List(ccsYY0Coincidences), ccsYYOtherCoincidences, List(ccsAll0Coincidences), ccsAllOtherCoincidences).map(statisticCoincidenceSection)
    val homTransposed = Range(0, homSections(0).size).map(_ => new Array[Double](homSections.size)).toArray
    homSections.zipWithIndex.foreach(z1 => z1._1.zipWithIndex.foreach(z2 => homTransposed(z2._2)(z1._2) = homSections(z1._2)(z2._2)))
    map.put(s"HOM Sections", homTransposed)
    benchMarker.foreach(b => b.tag("HOM Sections"))

    val channelMonitorSyncList = dataBlock.content(channelMonitorSyncChannel)
    map.put("ChannelMonitorSync", Array[Long](dataBlock.dataTimeBegin, dataBlock.dataTimeEnd) ++ (channelMonitorSyncList.size match {
      case s if s > 10 => {
        println("Error: counting rate at ChannelMonitorSyncChannel exceed 10!")
        new Array[Long](0)
      }
      case s => channelMonitorSyncList
    }))
    benchMarker.foreach(b => b.tag("CMS"))

    val countSections = Range(0, qberSectionCount).toArray.map(i => new Array[Int](2))
    List(monitorListAlice, monitorListBob).zipWithIndex.foreach(z => z._1.foreach(event => {
      val sectionIndex = ((event - dataBlock.dataTimeBegin).toDouble / (dataBlock.dataTimeEnd - dataBlock.dataTimeBegin) * qberSectionCount).toInt
      if (sectionIndex >= 0 && sectionIndex < qberSections.size) countSections(sectionIndex)(z._2) += 1
    }))
    map.put(s"Count Sections", countSections)
    benchMarker.foreach(b => b.tag("Count Sections"))
    benchMarker.foreach(b => b.tag("Finish"))

    map.toMap
  }

  private def analysisSingleChannel(triggerList: Array[Long], signalList: Array[Long], period: Double, delay: Double, gate: Double, pulseDiff: Double, randomNumberSize: Int) = {
    val triggerIterator = triggerList.iterator
    val currentTriggerRef = new AtomicLong(if (triggerIterator.hasNext) triggerIterator.next() else 0)
    val nextTriggerRef = new AtomicLong(if (triggerIterator.hasNext) triggerIterator.next() else Long.MaxValue)
    val meta = signalList.map(time => {
      while (time >= nextTriggerRef.get) {
        currentTriggerRef set nextTriggerRef.get
        nextTriggerRef.set(if (triggerIterator.hasNext) triggerIterator.next() else Long.MaxValue)
      }
      val pulseIndex = ((time - currentTriggerRef.get) / period).toLong
      val delta = (time - currentTriggerRef.get - period * pulseIndex).toLong
      val p = if (math.abs(delta - delay) < gate / 2) 0 else if (math.abs(delta - delay - pulseDiff) < gate / 2) 1 else -1
      ((currentTriggerRef.get / period / randomNumberSize).toLong, pulseIndex, p, currentTriggerRef.get)
    })
    meta
  }
}

object RandomNumber {
  def apply(rn: Int) = new RandomNumber(rn)

  val ALL_RANDOM_NUMBERS = Array(0, 1, 2, 3, 4, 5, 6, 7).map(RandomNumber(_))
}

class RandomNumber(val RN: Int) {
  def isVacuum = (RN / 2) == 0

  def isX = (RN / 2) == 1

  def isY = (RN / 2) == 2

  def isZ = (RN / 2) == 3

  def intensity = RN / 2

  def encode = RN % 2

  override def equals(obj: scala.Any): Boolean = obj match {
    case other: RandomNumber => other.RN == RN
    case _ => false
  }
}

class Coincidence(val r1: Int, val r2: Int, val randomNumberAlice: RandomNumber, val randomNumberBob: RandomNumber, val triggerTime: Long, val triggerIndex: Long, val pulseIndex: Long) {
  val basisMatched = randomNumberAlice.intensity == randomNumberBob.intensity
  val valid = (r1 == 0 && r2 == 1) || (r1 == 1 && r2 == 0)
  val isCorrect = randomNumberAlice.encode != randomNumberBob.encode
}

object DebugT {
  private val previousT = new AtomicLong(System.nanoTime())

  def tag(msg: String): Unit = {
    val currentT = System.nanoTime()
    val deltaT = currentT - previousT.get
    previousT set currentT
    println(f"${deltaT / 1e6}%.0f -- $msg")
  }
}