package com.interactionfree.display.w3html

import com.interactionfree.display._
import scala.collection.mutable
import scala.xml._
import com.interactionfree.display.DisplayNode._

object W3HTMLDisplay {
  private val htmlElementConverterMap = new mutable.HashMap[String, W3HTMLElementConvertor]()

  def registerHTMLElementConverter(convertor: W3HTMLElementConvertor) =
    htmlElementConverterMap(convertor.name.toLowerCase) = convertor

  DefaultW3HTMLElementConvertors.defaultConverters.foreach(registerHTMLElementConverter)

  private[w3html] def createW3HTML(displayNode: DisplayNode): Node = htmlElementConverterMap.get(displayNode.name) match {
    case None => throw new DisplayNodeException(s"<${displayNode.name}> is not a valid Display Node.")
    case Some(convertor) => convertor.convert(displayNode)
  }
}

class W3HTMLDisplay(val display: Display) {
  val title = display.title
  val content = new PrettyPrinter(80, 2).format(createW3HTML)

  private def createW3HTML = W3HTMLDisplay.createW3HTML(display.root)
}

object W3HTMLElementConvertor {
  private val emptyNamespaceBinding = NamespaceBinding(null, null, null)

  private def attributeSeparator(key: String) = key match {
    case "class" => " "
    case _ => ";"
  }
}

class W3HTMLElementConvertor(val name: String, val label: String, attr: List[Tuple2[String, String]] = List(), val textComponent: Boolean = false) {
  def convert(node: DisplayNode): Node = {
    val attributeTuples = attributes(node)
    val attributeMap = new mutable.HashMap[String, String]()
    attributeTuples.map(t => t._1).toSet.foreach(key =>
      attributeMap(key) = attributeTuples.filter(_._1 == key).map(_._2).mkString(W3HTMLElementConvertor.attributeSeparator(key)))
    val attr: List[MetaData] = attributeMap.map(z => new UnprefixedAttribute(z._1, z._2, Node.NoAttributes)).toList
    val att = attr.size match {
      case 0 => Node.NoAttributes
      case 1 => attr(0)
      case _ => attr.reduce((a, b) => MetaData.update(a, W3HTMLElementConvertor.emptyNamespaceBinding, b))
    }
    val children = this.children(node)
    Elem(null, label, att, W3HTMLElementConvertor.emptyNamespaceBinding, false, children: _*)
  }

  protected def attributes(node: DisplayNode): List[Tuple2[String, String]] = {
    val buffer = new mutable.ArrayBuffer[Tuple2[String, String]]()
    buffer ++= attr
    node.backgroundColor.foreach(backgroundColor => buffer += (("style", s"background-color:${backgroundColor.toWebString()}")))
    node.textColor.foreach(textColor => buffer += (("style", s"color:${textColor.toWebString()}")))
    if (textComponent) buffer += (("class", node.fontSize match {
      case DisplayNode.FontSize.TINY => "w3-tiny"
      case DisplayNode.FontSize.SMALL => "w3-small"
      case DisplayNode.FontSize.MEDIUM => "w3-medium"
      case DisplayNode.FontSize.LARGE => "w3-large"
      case DisplayNode.FontSize.XLARGE => "w3-xlarge"
      case DisplayNode.FontSize.XXLARGE => "w3-xxlarge"
      case DisplayNode.FontSize.XXXLARGE => "w3-xxxlarge"
      case DisplayNode.FontSize.JUMBO => "w3-jumbo"
    }))
    buffer.toList
  }

  protected def children(node: DisplayNode): Array[Node] = {
    val cs = node.children.map(W3HTMLDisplay.createW3HTML).toArray
    if (textComponent) cs ++ Array[Node]({
      val text = Text(node.text)
      node.fontStyle match {
        case DisplayNode.FontStyle.PLAIN => text
        case DisplayNode.FontStyle.BOLD => Elem(null, "b", Node.NoAttributes, W3HTMLElementConvertor.emptyNamespaceBinding, false, text)
        case DisplayNode.FontStyle.ITALIC => Elem(null, "i", Node.NoAttributes, W3HTMLElementConvertor.emptyNamespaceBinding, false, text)
        case DisplayNode.FontStyle.BOLD_ITALIC =>
          Elem(null, "b", Node.NoAttributes, W3HTMLElementConvertor.emptyNamespaceBinding, false,
            Elem(null, "i", Node.NoAttributes, W3HTMLElementConvertor.emptyNamespaceBinding, false, text))
      }
    }) else cs
  }
}

object DefaultW3HTMLElementConvertors {
  val defaultConverters = List(
    new W3HTMLElementConvertor("IFDisplay", "div"),
    new W3HTMLElementConvertor("container", "div", List(("class", "w3-container"))),
    new W3HTMLElementConvertor("label", "p", textComponent = true)
  )
}
