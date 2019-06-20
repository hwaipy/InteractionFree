package com.interactionfree.db

import com.interactionfree.core.MessageClient

import scala.xml.XML

object TestMain extends App {
  private val registryConf = XML.loadFile("registry.conf")
  private val dbConf = registryConf \ "mongodb"
  private val dbURL = (dbConf \ "url").text
  private val dbName = (dbConf \ "db").text
  private val dbCollection = (dbConf \ "collection").text
  private val ifConf = registryConf \ "interactionfree"
  private val ifURL = (ifConf \ "url").text
  private val ifServiceName = (ifConf \ "servicename").text

  val registryService = new RegistryService(dbURL, dbName, dbCollection)
  //  val client = MessageClient.createHttpClient(ifURL, ifServiceName, registryService)

  registryService.getWholeRegistry("TestRe3g.sub.sub")

  Thread.sleep(1000)
  registryService.close
  //  client.close
}