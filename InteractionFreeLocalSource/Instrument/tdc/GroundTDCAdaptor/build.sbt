name := "GroundTDCAdaptor"
version := "0.0.1"
scalaVersion := "2.13.3"
organization := "com.interactionfree.instrument"
libraryDependencies += "com.interactionfree" %% "interactionfreescala" % "1.0.1"
libraryDependencies += "com.interactionfree.instrument" %% "universaltdc" % "1.0.0"
libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.0" % "test"
scalacOptions ++= Seq("-feature")
scalacOptions ++= Seq("-deprecation")
