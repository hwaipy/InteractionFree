enablePlugins(JavaServerAppPackaging, UniversalDeployPlugin, WindowsPlugin, WindowsDeployPlugin)

name := """InteractionFreePlay"""
organization := "com.interactionfree"

version := "0.1.0"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.12.8"

crossScalaVersions := Seq("2.12.8", "2.11.12")

libraryDependencies += "com.interactionfree" %% "interactionfree" % "0.1.0"
libraryDependencies += guice
libraryDependencies += "org.scalatestplus.play" %% "scalatestplus-play" % "4.0.1" % Test
