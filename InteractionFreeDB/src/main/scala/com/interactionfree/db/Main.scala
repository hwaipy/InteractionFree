package com.interactionfree.db

import java.util.Date

object TestMain extends App {
  val rs = new RegistryService()
  val registryName = "TestRe3g.sub.sub"
  //  rs.setRegistry(registryName, "key1", "value1")
  //  rs.setRegistry(registryName, "set1.set2.key3", "value1")

  val key = "set1.set2.set3.key1"

//  rs.setRegistry(registryName, key, List(1.02, 2, Map("1" -> 3, "2" -> "not hello"), 4, new Date().toString))
  println(rs.getRegistry(registryName, key))

  Thread.sleep(1000)
}