package com.interactionfree.display

import java.awt.Color
import java.nio.file.Path
import java.util.concurrent.atomic.AtomicReference
import java.util.regex.Pattern

import scala.xml._
import scala.language.postfixOps
import DisplayNode._

object Display {
  def loadFromXMLFile(path: Path) = new Display(XML.loadFile(path.toFile))
}

class Display(rootNode: Node) {
  val root = DisplayNode.create(rootNode)
  if (root isnot "ifdisplay") throw new DisplayNodeException("The root element should be IFDisplay")
  val title = root.getAttribute("title").headOption.map(_.strip)
}

object DisplayNode {

  private val COLORS = Map(
    "amber" -> 0xffc107,
    "aqua" -> 0x00ffff,
    "blue" -> 0x2196F3,
    "light-blue" -> 0x87CEEB,
    "brown" -> 0x795548,
    "cyan" -> 0x00bcd4,
    "blue-grey" -> 0x607d8b,
    "green" -> 0x4CAF50,
    "light-green" -> 0x8bc34a,
    "indigo" -> 0x3f51b5,
    "khaki" -> 0xf0e68c,
    "lime" -> 0xcddc39,
    "orange" -> 0xff9800,
    "deep-orange" -> 0xff5722,
    "pink" -> 0xe91e63,
    "purple" -> 0x9c27b0,
    "deep-purple" -> 0x673ab7,
    "red" -> 0xf44336,
    "sand" -> 0xfdf5e6,
    "teal" -> 0x009688,
    "yellow" -> 0xffeb3b,
    "white" -> 0xffffff,
    "black" -> 0x000000,
    "grey" -> 0x9e9e9e,
    "light-grey" -> 0xf1f1f1,
    "dark-grey" -> 0x616161,
    "pale-red" -> 0xffdddd,
    "pale-green" -> 0xddffdd,
    "pale-yellow" -> 0xffffcc,
    "pale-blue" -> 0xddffff,
  ).map(z => (z._1, new Color(z._2)))
  private val COLOR_RGB_PATTERN = Pattern.compile("([0-9]+),([0-9]+),([0-9]+)")
  private val COLOR_WEB_PATTERN = Pattern.compile("#([0-9a-fA-F]+)")

  def create(node: Node, parent: DisplayNode = null): DisplayNode = {
    val name = node.label.toLowerCase
    val text = node.text
    val attributes = node.attributes.asAttrMap
    val displayNode = new DisplayNode(name, text, attributes, parent)
    val children = node.child.filter(_.isInstanceOf[Elem]).map(cn => create(cn, displayNode)).toList
    displayNode.appendChildren(children)
    displayNode
  }

  private def parseColor(colorString: String) = try {
    COLORS.get(colorString) match {
      case Some(color) => color
      case None => {
        val webMatcher = COLOR_WEB_PATTERN.matcher(colorString)
        if (webMatcher.find()) new Color(Integer.parseInt(webMatcher.group(1), 16))
        else {
          val rgbMatcher = COLOR_RGB_PATTERN.matcher(colorString)
          if (rgbMatcher.find()) new Color(rgbMatcher.group(1).toInt, rgbMatcher.group(2).toInt, rgbMatcher.group(3).toInt)
          else throw new DisplayNodeException(s"${colorString} is not a valid Color.")
        }
      }
    }
  } catch {
    case e: Throwable => throw new DisplayNodeException(s"${colorString} is not a valid Color.")
  }

  implicit class ColorToWeb(color: Color) {
    def toWebString() = {
      val hex = s"${(color.getRGB & 0x00ffffff).toHexString}"
      val empty = Range(0, 6 - hex.size).toList.map(i => "0").mkString("")
      "#" + empty + hex
    }

    def isDeepColor() = (color.getRed + color.getGreen + color.getBlue) / 3 < 128
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
  lazy val backgroundColor = getAttribute("color").headOption.map(DisplayNode.parseColor)
  lazy val textColor = getAttribute("text-color").headOption match {
    case Some(tc) => Some(DisplayNode.parseColor(tc))
    case None => backgroundColor.map(bc => if (bc.isDeepColor) DisplayNode.COLORS("white") else DisplayNode.COLORS("black"))
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