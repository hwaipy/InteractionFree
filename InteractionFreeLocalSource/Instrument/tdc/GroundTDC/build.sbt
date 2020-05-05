name := "GroundTDC"
version := "0.1.0"
scalaVersion := "2.13.2"
organization := "com.interactionfree.instrument"
libraryDependencies += "com.interactionfree" %% "interactionfreescala" % "0.1.0"
libraryDependencies += "org.scalatest" %% "scalatest" % "3.1.1" % "test"
scalacOptions ++= Seq("-feature")
scalacOptions ++= Seq("-deprecation")
