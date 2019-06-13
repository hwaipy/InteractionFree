package com.interactionfree.display

import java.nio.file.Path
import java.util.concurrent.atomic.AtomicReference
import scala.xml._
import scala.language.postfixOps

object Display {
  def loadFromXMLFile(path: Path) = new Display(XML.loadFile(path.toFile))
}

class Display(rootNode: Node) {
  val root = DisplayNode.create(rootNode)
  if (root isnot "ifdisplay") throw new DisplayNodeException("The root element should be IFDisplay")
  val title = root.getAttribute("title").headOption.map(_.strip)
}

object DisplayNode {

  val colors = Map( //name -> (code, isALightColor)  //true for 000, false for fff
    "amber" -> (0xffc107, true),
    "aqua" -> (0x00ffff, true),
    "blue" -> (0x2196F3, false),
    "light-blue" -> (0x87CEEB, true),
    "brown" -> (0x795548, false),
    "cyan" -> (0x00bcd4, true),
    "blue-grey" -> (0x607d8b, false),
    "green" -> (0x4CAF50, false),
    "light-green" -> (0x8bc34a, true),
    "indigo" -> (0x3f51b5, false),
    "khaki" -> (0xf0e68c, true),
    "lime" -> (0xcddc39, true),
    "orange" -> (0xff9800, true),
    "deep-orange" -> (0xff5722, false),
    "pink" -> (0xe91e63, false),
    "purple" -> (0x9c27b0, false),
    "deep-purple" -> (0x673ab7, false),
    "red" -> (0xf44336, false),
    "sand" -> (0xfdf5e6, true),
    "teal" -> (0x009688, false),
    "yellow" -> (0xffeb3b, true),
    "white" -> (0xffffff, true),
    "black" -> (0x000000, false),
    "grey" -> (0x9e9e9e, true),
    "light-grey" -> (0xf1f1f1, true),
    "dark-grey" -> (0x616161, false),
    "pale-red" -> (0xffdddd, true),
    "pale-green" -> (0xddffdd, true),
    "pale-yellow" -> (0xffffcc, true),
    "pale-blue" -> (0xddffff, true),
  )

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

  private def parseColor(colorString: String) = {
    println(colorString)
    ""
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
  lazy val backgroundColor = getAttribute("color", true).headOption.map(DisplayNode.parseColor)
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
  println(backgroundColor)
}

class DisplayNodeException(message: String) extends Exception(message)