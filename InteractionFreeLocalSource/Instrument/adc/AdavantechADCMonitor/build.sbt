name := "ADCMonitor"
version := "1.0.3"
scalaVersion := "2.13.3"
organization := "com.interactionfree"
libraryDependencies += "org.scala-lang" % "scala-reflect" % "2.13.3"
libraryDependencies += "org.scala-lang" % "scala-compiler" % "2.13.3"
libraryDependencies += "com.interactionfree" %% "interactionfreescala" % "1.0.0"
scalacOptions ++= Seq("-feature")
scalacOptions ++= Seq("-deprecation")
//fork := true