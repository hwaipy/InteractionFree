# TDC DataBlock Serialization

## DataBlock

A DataBlock is a data structure that describe TDC events in a certain duration, which contain the following information:

`creationTime`: Specify the absolute time of data fetching. The accuracy is normally < 1 s.

`resolution`: Specify the time unit of `dataTimeBegin`, `dataTimeEnd`, and `content`.

`dataTimeBegin`: Specify the begin of the DataBlock relative to the TDC time.

`dataTimeEnd`: Specify the end of the DataBlock relative to the TDC time. Has the same resolution with `dataTimeBegin`. `dataTimeEnd` is required to be larger than `dataTimeBegin`.

`content`: TDC events. For each event, `time` and `channel` is specified. `time` is required to be bewteen `dataTimeBegin` and `dataTimeEnd`.  `channel` start with `0`.

`released`: To prevent memory leak, a DataBlock is allowed to be RELEASED. In this case, `content` will be empty. The DataBlock itself still remains to notify the program that "there was a DataBlock" but the information of events are lost. 

`sizes`: A list of integer that specify the number of events in each channel. This information is useful when the DataBlock is RELEASED.

## Protocol_V1

The entire DataBlock should be serialized by [MsgPack](https://msgpack.org) as follows:

```
{
	"Format": "DataBlock_V1",
	"CreationTime": $creationTime,
	"Resolution": $resolution,
	"DataTimeBegin": $dataTimeBegin,
	"DataTimeEnd": $dataTimeEnd,
	"Sizes": $sizes,
	"Content": $serializedContent
}
```

`creationTime`: `Long`. milliseconds from midnight, January 1, 1970 UTC (coordinated universal time).

`resolution`: `Float`. Second. For example, 1 ps is `1e-12`.

`dataTimeBegin`, `dataTimeEnd`: `Long`. Picosecond. For example, 1 ms with `resolution` of `16` is `62,500,000`.

`sizes`: `Array[Int]`.

`$serializedContent`: `Array[Array[Array[Byte]]]`. This is the key of DataBlock serialization. The `content` should be serialized channel by channel. For each channel, the events are sliced into fragments to enhence the capacity of parallelism. The size of each fragment is recommand to be 100000, yet not restricted. Each fragment of events is serialized as `Array[Byte]`, thus a channel of events is serialized as  `Array[Array[Byte]]`. Each fragment is serialized as follows:

1. Suppose there is `N` events in total. Record the first time as `TIME_FIRST`.
2. Calculate time differents between neighbor events. `delta[i] = time[i+1] - time[i]`, `i=0` to `N-1`.
3. Calculate data length for each delta. `len[i]` = $log_{16}(delta[i])$.
 


$$
7^7
$$


1 -> 16 -> 16 ps
2 -> 256 -> 0.256 ns
3 -> 4096 -> 4 ns
4 -> 65536 -> 65 ns
5 -> 1048576 -> 1 us
6 -> 16777216 -> 16 us
7 -> 268435456 -> 268 us
8 -> 4.29 ms
9 -> 68.7 ms
10-> 1.1 s
15-> 
