package com.interactionfree.db

import com.interactionfree.db.TestMain.registryName
import org.bson.BsonType
import org.mongodb.scala._
import org.mongodb.scala.bson.BsonValue
import org.mongodb.scala.model.Filters._
import org.mongodb.scala.model.Updates._
import org.mongodb.scala.model.Projections._
import org.mongodb.scala.model.Sorts._

import scala.collection.mutable
import scala.concurrent.{Await, Future}
import scala.concurrent.duration._
import scala.language.postfixOps
import scala.collection.JavaConverters._
import scala.collection.mutable.ArrayBuffer

object RegistryService {
  val KEY_NAME = "_name"

  implicit class AwaitUtil[T](observable: Observable[T]) {
    def await = RegistryService.await(observable)
  }

  private def await[T](observable: Observable[T], atMost: Duration = 10 seconds): Seq[T] = await(observable.toFuture, atMost)

  private def await[T](future: Future[T], atMost: Duration): T = try {
    Await.result(future, atMost)
  } catch {
    case e: InterruptedException => throw new IllegalStateException("Error in Registry: StoreService not responsed.")
    case e: Throwable => throw new RuntimeException("Exception in Registry Service.", e)
  }
}

class RegistryService {

  import RegistryService._

  private val mongoClient: MongoClient = MongoClient()
  private val database: MongoDatabase = mongoClient.getDatabase("InteractionFree")
  private val collection: MongoCollection[Document] = database.getCollection("Registry")

  val validRegisties = new mutable.HashSet[String]()
  validRegisties ++= collection.find().await.map(doc => doc.get("_name")).flatten.filter(_.isString).map(_.asString.getValue)

  private def validateRegistry(name: String) = if (!validRegisties.contains(name)) {
    if (collection.find(equal(RegistryService.KEY_NAME, name)).first().await.isEmpty)
      collection.insertOne(Document(RegistryService.KEY_NAME -> registryName)).await
    validRegisties += name
  }

  private def validateKey(key: String) =
    if (key.startsWith("_")) throw new IllegalArgumentException("Key should not start with '_'")

  def setRegistry(name: String, key: String, value: Any): Unit = {
    validateRegistry(name)
    validateKey(key)
    collection.updateOne(equal(RegistryService.KEY_NAME, name), set(key, value)).await
  }

  def getRegistry(name: String, key: String, inherit: Boolean = true) = {
    validateRegistry(name)
    validateKey(key)
    val nameFilter = inherit match {
      case true => {
        val nameItems = name.split("\\.").toList
        val names = Range(0, nameItems.size).map(i => nameItems.slice(0, i + 1).mkString(".")).reverse
        or(names.map(n => equal(RegistryService.KEY_NAME, n)): _*)
      }
      case false => equal(RegistryService.KEY_NAME, name)
    }
    collection.find(and(nameFilter, exists(key))).sort(descending(RegistryService.KEY_NAME))
      .projection(include(key)).first.await.headOption match {
      case None => null
      case Some(doc) => {
        println(doc)
        val value = key.split("\\.").foldLeft[BsonValue](doc.toBsonDocument)((d, s) => {
          d.asDocument.get(s)
        })
        decodeBsonValue(value)
      }
    }
  }

  private def decodeBsonValue(value: BsonValue): Any = {
    value.getBsonType match {
      case BsonType.DOUBLE => value.asDouble.getValue
      case BsonType.INT32 => value.asInt32.getValue
      case BsonType.INT64 => value.asInt64.getValue
      case BsonType.STRING => value.asString.getValue
      case BsonType.BOOLEAN => value.asBoolean.getValue
      case BsonType.NULL => null
      case BsonType.ARRAY => value.asArray.iterator.asScala.toList.map(decodeBsonValue)
      case BsonType.DOCUMENT => value.asDocument.iterator.map(e => (e._1, decodeBsonValue(e._2))).toMap
      case _ => throw new IllegalStateException(s"BsonValue not valid for Registry: ${value}")
    }
  }
}
