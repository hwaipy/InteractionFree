package com.interactionfree.io

import java.nio.ByteBuffer

import com.interactionfree.core.Message

trait MessageEncoder {
  def feed(msg: Message): MessageEncoder

  def pack(): Array[Byte]
}

trait MessageDecoder {
  def feed(feed: ByteBuffer): Int

  def next(): Option[Message]
}
