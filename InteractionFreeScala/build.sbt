name := "InteractionFreeScala"
version := "1.0.0"
scalaVersion := "2.13.3"
organization := "com.interactionfree"
libraryDependencies += "org.scala-lang" % "scala-reflect" % "2.13.3"
libraryDependencies += "org.scala-lang" % "scala-compiler" % "2.13.3"
libraryDependencies += "org.msgpack" % "msgpack-core" % "0.8.20"
libraryDependencies += "org.msgpack" % "jackson-dataformat-msgpack" % "0.8.20"
libraryDependencies += "org.zeromq" % "jeromq" % "0.5.2"
libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.0" % "test"
scalacOptions ++= Seq("-feature")
scalacOptions ++= Seq("-deprecation")
