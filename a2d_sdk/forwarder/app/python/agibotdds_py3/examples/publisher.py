#!/usr/bin/env python3
import time
from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.sample_pb2 import SampleMessage


def test_publisher_class():
    """
    Test publisher.
    """
    print("=" * 120)
    msg = SampleMessage()
    test_node = agibotdds.Node("publisher")
    # user-defined QoS
    qos = agibotdds.qos(reliability=agibotdds.qos.Reliability.BEST_EFFORT, depth=10,
                 history=agibotdds.qos.History.KEEP_ALL, durability=agibotdds.qos.Durability.TRANSIENT_LOCAL)

    publisher = test_node.create_publisher(
        "agibotdds_py3/sample", SampleMessage, qos)
    while not agibotdds.is_shutdown():
        time.sleep(1)
        msg.id = msg.id + 1
        print("=" * 80)
        print("publisher msg ->")
        print("%s" % msg)
        publisher.publish(msg)


if __name__ == '__main__':
    agibotdds.init("publisher")
    test_publisher_class()
    agibotdds.shutdown()
