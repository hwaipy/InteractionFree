package com.interactionfree.core

import java.awt.Desktop
import java.io.{File, PrintWriter}
import java.nio.file.{Files, Paths}
import java.util.concurrent.atomic.AtomicReference

import com.interactionfree.display.Display
import com.interactionfree.display.w3html.W3HTMLDisplay

import scala.io.Source

object Main extends App {
  val display = Display.loadFromXMLFile(Paths.get("res/default.xml"))
  val w3HTMLDisplay = new W3HTMLDisplay(display)

  val html = new AtomicReference[String](Source.fromFile("res/default.html").getLines().mkString(System.lineSeparator()))

  html set (html.get.replaceFirst("#W3HTML_TITLE#", w3HTMLDisplay.title match {
    case Some(t) => t
    case None => "No Title"
  }))
  html set (html.get.replaceFirst("#W3HTML_CONTENT#", w3HTMLDisplay.content))
  println(w3HTMLDisplay.content)

  val testPageDirectory = Paths.get("target/testpage/")
  if (Files.notExists(testPageDirectory)) Files.createDirectories(testPageDirectory)
  val testPagePath = testPageDirectory.resolve("default.html")
  val pw = new PrintWriter(testPagePath.toFile)
  pw.print(html)
  pw.close()

  //Desktop.getDesktop
  //Desktop.getDesktop.open(testPagePath.toFile)
}