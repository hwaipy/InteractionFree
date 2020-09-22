package com.interactionfree.instrument.tdc

import java.util.concurrent.atomic.AtomicInteger

object BenchMarker extends App {
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

  run()
}