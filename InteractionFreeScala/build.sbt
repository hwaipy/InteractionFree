name := "InteractionFreeScala"
version := "0.1.0"
scalaVersion := "2.13.2"
organization := "com.interactionfree"
libraryDependencies += "org.scala-lang" % "scala-reflect" % "2.13.2"
libraryDependencies += "org.scala-lang" % "scala-compiler" % "2.13.2"
libraryDependencies += "org.msgpack" % "msgpack-core" % "0.8.20"
libraryDependencies += "org.msgpack" % "jackson-dataformat-msgpack" % "0.8.20"
libraryDependencies += "org.zeromq" % "jeromq" % "0.5.2"
//libraryDependencies += "com.typesafe.akka" %% "akka-actor" % "2.6.5"
libraryDependencies += "org.scalatest" %% "scalatest" % "3.1.1" % "test"
scalacOptions ++= Seq("-feature")
scalacOptions ++= Seq("-deprecation")

// https://mvnrepository.com/artifact/eu.neilalexander/jnacl
libraryDependencies += "eu.neilalexander" % "jnacl" % "1.0.0"
