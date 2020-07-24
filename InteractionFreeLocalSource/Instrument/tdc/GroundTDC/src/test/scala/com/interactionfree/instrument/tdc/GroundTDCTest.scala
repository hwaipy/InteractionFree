package com.interactionfree.instrument.tdc

import java.io.IOError
import org.scalatest.BeforeAndAfter
import org.scalatest.funsuite.AnyFunSuite
import scala.collection.mutable.ListBuffer
import scala.concurrent.Await
import scala.concurrent.duration._
import scala.language.postfixOps

class GroundTDCTest extends AnyFunSuite with BeforeAndAfter {
  test("Test Dynamic Invoker.") {
    //    val worker = new IFWorker(brokerAddress)
    //    val invoker = worker.toMessageInvoker()
    //    val m1 = invoker.fun1(1, 2, "3", b = None, c = List(1, 2, "3d"))
    //    assert(m1.isBrokerMessage)
    //    val m1Invocation = m1.invocation
    //    assert(m1Invocation.isRequest)
    //    assert(m1Invocation.getFunction == "fun1")
    //    assert(m1Invocation.getArguments == List(1, 2, "3"))
    //    assert(m1Invocation.getKeywordArguments == Map("b" -> None, "c" -> List(1, 2, "3d")))
    //    val invoker2 = worker.toMessageInvoker("OnT")
    //    val m2 = invoker2.fun2()
    //    val m2Invocation = m2.invocation
    //    assert(m2Invocation.isRequest)
    //    assert(m2Invocation.getFunction == "fun2")
    //    assert(m2Invocation.getArguments == Nil)
    //    assert(m2Invocation.getKeywordArguments == Map())
    //    assert(m2.isServiceMessage)
    //    assert(m2.remoteAddress sameElements "OnT".getBytes("UTF-8"))
    //    worker.close()
  }
}
