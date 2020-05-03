package com.interactionfree

import java.math.BigInteger
import java.nio.ByteBuffer
import java.util.concurrent.atomic.{AtomicBoolean, AtomicInteger, AtomicLong}
import org.msgpack.core.MessagePack
import org.msgpack.value.Value
import scala.collection.mutable
import scala.collection.mutable.ListBuffer
import scala.reflect.runtime.currentMirror
import scala.reflect.runtime.universe._

object Invocation {
  val KeyType = "Type"
  val KeyFunciton = "Function"
  val KeyArguments = "Arguments"
  val KeyKeyworkArguments = "KeyworkArguments"
  val KeyRespopnseID = "ResponseID"
  val KeyResult = "Result"
  val KeyError = "Error"
  val KeyWarning = "Warning"
  val ValueTypeRequest = "Request"
  val ValueTypeResponse = "Response"
  val Preserved = List(KeyType, KeyFunciton, KeyArguments, KeyKeyworkArguments, KeyRespopnseID, KeyResult, KeyError, KeyWarning)
  protected[interactionfree] val maxDeepth = 100

  def newRequest(functionName: String, args: List[Any] = Nil, kwargs: Map[String, Any] = Map()) = new Invocation(Map(
    Invocation.KeyType -> ValueTypeRequest,
    Invocation.KeyFunciton -> functionName,
    Invocation.KeyArguments -> args,
    Invocation.KeyKeyworkArguments -> kwargs
  ))

  def newResponse(messageID: Array[Byte], result: Any) = new Invocation(Map(
    Invocation.KeyType -> Invocation.ValueTypeResponse,
    Invocation.KeyRespopnseID -> messageID,
    Invocation.KeyResult -> result
  ))

  def newError(messageID: Array[Byte], description: String) = new Invocation(Map(
    Invocation.KeyType -> Invocation.ValueTypeResponse,
    Invocation.KeyRespopnseID -> messageID,
    Invocation.KeyError -> description
  ))

  def deserialize(bytes: Array[Byte], serialization: String = "Msgpack") = serialization match {
    case "Msgpack" => {
      val unpacker = org.msgpack.core.MessagePack.newDefaultUnpacker(bytes)
      val value = unpacker.unpackValue()
      val map = convert(value).asInstanceOf[Map[String, Any]]
      new Invocation(map)
    }
    case _ => throw new IFException(s"Bad serialization: ${serialization}")
  }

  private def convert(value: Value, deepth: Int = 0): Any = {
    if (deepth > maxDeepth) throw new IllegalArgumentException("Message over deepth.")
    import org.msgpack.value.ValueType._
    value.getValueType match {
      case ARRAY => {
        val arrayValue = value.asArrayValue
        val list: ListBuffer[Any] = ListBuffer()
        val it = arrayValue.iterator
        while (it.hasNext) {
          list += convert(it.next, deepth + 1)
        }
        list.toList
      }
      case MAP => {
        val mapValue = value.asMapValue
        val map: mutable.HashMap[Any, Any] = new mutable.HashMap
        val it = mapValue.entrySet.iterator
        while (it.hasNext) {
          val entry = it.next
          map += (convert(entry.getKey, deepth + 1) -> convert(entry.getValue, deepth + 1))
        }
        map.toMap
      }
      case BINARY => value.asBinaryValue.asByteArray
      case BOOLEAN => value.asBooleanValue.getBoolean
      case FLOAT => value.asFloatValue.toDouble
      case INTEGER => {
        val integerValue = value.asIntegerValue
        if (integerValue.isInLongRange) {
          if (integerValue.isInIntRange) {
            integerValue.toInt
          } else {
            integerValue.toLong
          }
        } else {
          BigInt.javaBigInteger2bigInt(integerValue.asBigInteger)
        }
      }
      case NIL => None
      case STRING => value.asStringValue.toString
      case _ => throw new IllegalArgumentException(s"Unknown ValueType: ${value.getValueType}")
    }
  }
}

class Invocation(private val content: Map[String, Any]) {

  def get(key: String) = content.get(key)

  def apply(key: String) = content(key)

  def isRequest = content(Invocation.KeyType) == Invocation.ValueTypeRequest

  def isResponse = content(Invocation.KeyType) == Invocation.ValueTypeResponse

  def isError = isResponse && content.contains(Invocation.KeyError)

  def hasWarning = isResponse && content.contains(Invocation.KeyWarning)

  def getFunction = if (isRequest) content(Invocation.KeyFunciton).asInstanceOf[String] else throw new IFException("Not a Request.")

  def getArguments = if (isRequest) content.get(Invocation.KeyArguments) match {
    case Some(args) => args match {
      case a: List[_] => a
      case a => List(a)
    }
    case None => Nil
  } else throw new IFException("Not a Request.")

  def getKeywordArguments = if (isRequest) content.get(Invocation.KeyKeyworkArguments) match {
    case Some(kwargs) => kwargs.asInstanceOf[Map[String, Any]]
    case None => Map[String, Any]()
  } else throw new IFException("Not a Request.")

  def getResult = if (isResponse && !isError) content(Invocation.KeyResult) else throw new IFException("Not a valid Response.")

  def getWarning = if (isResponse) content(Invocation.KeyWarning).asInstanceOf[String] else throw new IFException("Not a Response.")

  def getError = if (isError) content(Invocation.KeyError).asInstanceOf[String] else throw new IFException("Not an Error.")

  def getResponseID = if (isResponse) content(Invocation.KeyRespopnseID).asInstanceOf[Array[Byte]] else throw new IFException("Not a Response.")

  def serialize(serialization: String = "Msgpack") = serialization match {
    case "Msgpack" => {
      val packer = org.msgpack.core.MessagePack.newDefaultBufferPacker

      def doFeed(value: Any, deepth: Int = 0, target: Option[String] = null): Unit = {
        if (deepth > Invocation.maxDeepth) {
          throw new IFException("Message over deepth.")
        }
        value match {
          case n if n == null || n == None => packer.packNil
          case i: Int => packer.packInt(i)
          case i: AtomicInteger => packer.packInt(i.get)
          case s: String => packer.packString(s)
          case b: Boolean => packer.packBoolean(b)
          case b: AtomicBoolean => packer.packBoolean(b.get)
          case l: Long => packer.packLong(l)
          case l: AtomicLong => packer.packLong(l.get)
          case s: Short => packer.packShort(s)
          case c: Char => packer.packShort(c.toShort)
          case b: Byte => packer.packByte(b)
          case f: Float => packer.packFloat(f)
          case d: Double => packer.packDouble(d)
          case bi: BigInteger => packer.packBigInteger(bi)
          case bi: BigInt => packer.packBigInteger(bi.bigInteger)
          case bytes: Array[Byte] => {
            packer.packBinaryHeader(bytes.length)
            packer.writePayload(bytes)
          }
          case array: Array[_] => {
            packer.packArrayHeader(array.length)
            for (i <- Range(0, array.length)) {
              doFeed(array(i), deepth + 1, target)
            }
          }
          case seq: Seq[_] => {
            packer.packArrayHeader(seq.size)
            seq.foreach(i => doFeed(i, deepth + 1, target))
          }
          case set: Set[_] => {
            packer.packArrayHeader(set.size)
            set.foreach(i => doFeed(i, deepth + 1, target))
          }
          case set: java.util.Set[_] => {
            packer.packArrayHeader(set.size)
            val it = set.iterator
            while (it.hasNext) {
              doFeed(it.next, deepth + 1, target)
            }
          }
          case list: java.util.List[_] => {
            packer.packArrayHeader(list.size)
            val it = list.iterator
            while (it.hasNext) {
              doFeed(it.next, deepth + 1, target)
            }
          }
          case map: scala.collection.Map[_, Any] => {
            packer.packMapHeader(map.size)
            map.foreach(entry => {
              doFeed(entry._1, deepth + 1, target)
              doFeed(entry._2, deepth + 1, target)
            })
          }
          case map: java.util.Map[_, _] => {
            packer.packMapHeader(map.size)
            val it = map.entrySet.iterator
            while (it.hasNext) {
              val entry = it.next
              doFeed(entry.getKey, deepth + 1, target)
              doFeed(entry.getValue, deepth + 1, target)
            }
          }
          case unit if (unit == () || unit == scala.runtime.BoxedUnit.UNIT) => packer.packNil
          case p: Product => {
            packer.packArrayHeader(p.productArity)
            val it = p.productIterator
            while (it.hasNext) {
              doFeed(it.next, deepth + 1, target)
            }
          }
          case _ => throw new IFException(s"Unrecognized value: ${value}")
        }
      }

      doFeed(content)
      packer.toByteArray
    }
    case _ => throw new IFException(s"Bad serialization: ${serialization}")
  }

  override def equals(obj: Any): Boolean = {
    if (!obj.isInstanceOf[Invocation]) false
    eq(obj.asInstanceOf[Invocation].content, content)
  }

  override def toString: String =
    if (isRequest) s"Request: ${getFunction} $getArguments $getKeywordArguments"
    else if (isError) s"Error ${new String(getResponseID)} $getError"
    else s"Response ${new String(getResponseID)} $getResult"

  def perform(target: Any) = {
    require(isRequest)
    val name = getFunction
    val args = getArguments
    val kwargs = getKeywordArguments
    val members = currentMirror.classSymbol(target.getClass).toType.members.collect {
      case m: MethodSymbol => m
    }
    val instanceMirror = currentMirror.reflect(target)
    val typeSignature = instanceMirror.symbol.typeSignature
    val methods = members.collect {
      case m if (m.name.toString == name) => matchParameters(m, args, kwargs, instanceMirror, typeSignature)
    }
    if (methods.size == 0) throw new IFException(s"Function not valid: ${name}.")
    val valids = methods.collect {
      case m: Option[(Any, Any)] if m != None => m
    }
    valids.size match {
      case 0 => throw new IFException(s"Function not valid: ${name}.")
      case _ => {
        val methodInstance = instanceMirror.reflectMethod(valids.head.get._1)
        try methodInstance(valids.head.get._2: _*)
        catch {
          case e: Throwable => throw new IFException(s"Failed to invoke ${name}: ${e.getCause.getMessage}", e)
        }
      }
    }
  }

  private def matchParameters(method: MethodSymbol, args: List[Any], kwargs: Map[String, Any], instanceMirror: InstanceMirror, typeSignature: Type) = {
    val paramInfo = (for (ps <- method.paramLists; p <- ps) yield p).zipWithIndex.map({ p =>
      (p._1.name.toString, p._1.asTerm.isParamWithDefault,
        typeSignature member TermName(s"${method.name}$$default$$${p._2 + 1}") match {
          case defarg if defarg != NoSymbol => Some((instanceMirror reflectMethod defarg.asMethod) ())
          case _ => None
        })
    }).drop(args.size)
    val paramMatches = paramInfo.collect {
      case info if kwargs.contains(info._1) => Some(kwargs(info._1))
      case info if info._2 => info._3
      case info => None
    }
    paramMatches.contains(None) match {
      case true => None
      case false => Some((method, args ::: paramMatches.map(p => p.get)))
    }
  }

  private def eq(a: Any, b: Any): Boolean = {
    def tryWrapInList(v: Any): Option[List[Any]] = {
      val list: ListBuffer[Any] = ListBuffer()
      v match {
        case array: Array[_] => {
          for (i <- Range(0, array.length)) {
            list += array(i)
          }
        }
        case seq: Seq[_] => list.appendAll(seq)
        case set: Set[_] => list.appendAll(set)
        case set: java.util.Set[_] => {
          val it = set.iterator
          while (it.hasNext) {
            list += it.next
          }
        }
        case l: java.util.List[_] => {
          val it = l.iterator
          while (it.hasNext) {
            list += it.next
          }
        }
        case _ => return None
      }
      Some(list.toList)
    }

    def tryWrapInMap(v: Any): Option[Map[String, Any]] = {
      val hm: collection.mutable.HashMap[String, Any] = collection.mutable.HashMap()
      v match {
        case map: scala.collection.Map[_, Any] => map.foreach(entry => {
          hm += (entry._1.toString -> entry._2)
        })
        case map: java.util.Map[_, _] => {
          val it = map.entrySet.iterator
          while (it.hasNext) {
            val entry = it.next
            hm += (entry.getKey.toString -> entry.getValue)
          }
        }
        case _ => return None
      }
      Some(hm.toMap)
    }

    def mapEq(mapA: Map[String, Any], mapB: Map[String, Any]): Boolean = {
      if (mapA.size != mapB.size) return false
      for ((k, v) <- mapA) {
        if (!mapB.contains(k)) return false
        if (!eq(v, mapB.get(k).get)) return false
      }
      return true
    }

    val listSomeA = tryWrapInList(a)
    val listSomeB = tryWrapInList(b)
    val mapSomeA = tryWrapInMap(a)
    val mapSomeB = tryWrapInMap(b)
    if (listSomeA != None && listSomeB != None) {
      return listSomeA.get == listSomeB.get
    }
    if (mapSomeA != None && mapSomeB != None) {
      return mapEq(mapSomeA.get, mapSomeB.get)
    }
    if ((a == None || a == null || a == ()) && (b == None || b == null || b == ())) return true
    if ((a.isInstanceOf[BigInteger] || a.isInstanceOf[BigInt]) && (b.isInstanceOf[BigInteger] || b.isInstanceOf[BigInt])) {
      return (a match {
        case bi: BigInteger => BigInt.javaBigInteger2bigInt(bi)
        case bi: BigInt => bi
      }) == (b match {
        case bi: BigInteger => BigInt.javaBigInteger2bigInt(bi)
        case bi: BigInt => bi
      })
    }
    return a == b
  }
}
