package com.interactionfree.display

import java.nio.file.Path
import java.util.concurrent.atomic.AtomicReference
import scala.collection.mutable
import scala.xml._
import scala.language.postfixOps

object Display {
  def loadFromXMLFile(path: Path) = new Display(XML.loadFile(path.toFile))
}

class Display(rootNode: Node) {
  val root = DisplayNode.create(rootNode)
  if (root isnot "ifdisplay") throw new DisplayNodeException("The root element should be IFDisplay")
  val title = root.getAttribute("title").headOption.map(_.strip)

  //println(root.children(0).children(0).children(0).name)
  //println(root.children(0).children(0).children(0).fontSize)
  //println(root.children(0).children(0).children(0).fontStyle)
}

object DisplayNode {

  def create(node: Node, parent: DisplayNode = null): DisplayNode = {
    val name = node.label.toLowerCase
    val text = node.text
    val attributes = node.attributes.asAttrMap
    val displayNode = new DisplayNode(name, text, attributes, parent)
    val children = node.child.filter(_.isInstanceOf[Elem]).map(cn => create(cn, displayNode)).toList
    displayNode.appendChildren(children)
    displayNode
  }

  object FontSize extends Enumeration {
    type FontSize = Value
    val TINY = Value("tiny")
    val SMALL = Value("small")
    val MEDIUM = Value("medium")
    val LARGE = Value("large")
    val XLARGE = Value("xlarge")
    val XXLARGE = Value("xxlarge")
    val XXXLARGE = Value("xxxlarge")
    val JUMBO = Value("jumbo")

    def getValue(name: String) =
      values.map(fs => fs.toString).contains(name) match {
        case true => Some(withName(name))
        case false => None
      }
  }

  object FontStyle extends Enumeration {
    type FontStyle = Value
    val PLAIN = Value("plain")
    val BOLD = Value("bold")
    val ITALIC = Value("italic")
    val BOLD_ITALIC = Value("bold italic")

    def getValue(name: String) =
      values.map(fs => fs.toString).contains(name) match {
        case true => Some(withName(name))
        case false => None
      }
  }

}

class DisplayNode(val name: String, val text: String, attributesO: Map[String, String], parentO: DisplayNode = null) {
  lazy val fontSize = fontAttributes.flatten.map(DisplayNode.FontSize.getValue).filter(_.isDefined).headOption match {
    case Some(fs) => fs.get
    case None => DisplayNode.FontSize.MEDIUM
  }
  lazy val fontStyle = fontAttributes.map(fas => fas.map(DisplayNode.FontStyle.getValue).filter(_.isDefined).map(_.get)).filter(_.nonEmpty).headOption match {
    case Some(fs) =>
      if (fs.contains(DisplayNode.FontStyle.BOLD)) if (fs.contains(DisplayNode.FontStyle.ITALIC)) DisplayNode.FontStyle.BOLD_ITALIC else DisplayNode.FontStyle.BOLD
      else if (fs.contains(DisplayNode.FontStyle.ITALIC)) DisplayNode.FontStyle.ITALIC else DisplayNode.FontStyle.PLAIN
    case None => DisplayNode.FontStyle.PLAIN
  }
  val childrenRef = new AtomicReference[List[DisplayNode]](List())
  val parent = parentO match {
    case null => None
    case p => Some(p)
  }
  val attributes = attributesO.map(e => (e._1.toLowerCase, e._2))
  private val fontAttributes = getAttribute("font", true).map(_.toLowerCase.split(" *, *").toList).filter(_.nonEmpty)

  def children = childrenRef get

  def getAttribute(key: String, inherit: Boolean = false): List[String] = inherit match {
    case false => attributes.get(key).toList
    case true => attributes.get(key).toList ++ parent.toList.map(p => p.getAttribute(key, inherit)).flatten
  }

  def is(name: String) = this.name.toLowerCase == name.toLowerCase

  def isnot(name: String) = this.name.toLowerCase != name.toLowerCase

  private def appendChildren(children: List[DisplayNode]) = childrenRef set (childrenRef.get ++ children)

  private def splitAttribute(key: String) = attributes.get(key) match {
    case Some(fa) => fa.split(" *, *").toList.map(_.toLowerCase)
    case None => List[String]()
  }
}

class DisplayNodeException(message: String) extends Exception(message)