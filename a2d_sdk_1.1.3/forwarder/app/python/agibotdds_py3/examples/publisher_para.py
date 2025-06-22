#!/usr/bin/env python3
import time
from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.agibotdds_test_messages_meta_pb2 import TestMeta

def test_publisher_class():
    """
    Test publisher.
    """
    print("=" * 120)
    msg = TestMeta()
    test_node = agibotdds.Node("publisher")
    # user-defined QoS
    qos = agibotdds.qos(reliability=agibotdds.qos.Reliability.BEST_EFFORT, depth=10,
                 history=agibotdds.qos.History.KEEP_ALL, durability=agibotdds.qos.Durability.TRANSIENT_LOCAL)

    num = 1
    seq = 0
    interval = 20
    last_heartbeat = agibotdds.Time.ptp(agibotdds.Preceision.Microseconds)
    publisher = test_node.create_publisher(
        "topic/test" + str(num), TestMeta, qos)
    while not agibotdds.is_shutdown():
        time.sleep(interval / 1000)
        msg.name = "00000000"
        msg.process = str(num)
        msg.timestamp = agibotdds.Time.ptp(agibotdds.Preceision.Microseconds)
        msg.pid = seq
        msg.last_heartbeat = last_heartbeat
        msg.interval = interval
        msg.counter = seq
        # size = msg.ByteSizeLong()
        print(f"publish: {num} {interval} {seq} {msg.timestamp}")
        print("%s" % msg)
        publisher.publish(msg)
        seq += 1
        last_heartbeat = msg.timestamp


if __name__ == '__main__':
    agibotdds.init("publisher")
    test_publisher_class()
    agibotdds.shutdown()
