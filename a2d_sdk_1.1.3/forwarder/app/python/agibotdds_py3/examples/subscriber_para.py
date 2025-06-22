#!/usr/bin/env python3

from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.agibotdds_test_messages_meta_pb2 import TestMeta


def callback(data):
    """
    Subscriber message callback.
    """
    print("=" * 80)
    print(f"subscriber: {data.process} {data.pid} {data.timestamp}")
    # print(data)


def test_subscriber_class():
    """
    Subscriber message.
    """
    print("=" * 120)
    # default QoS
    qos = agibotdds.qos()
    test_node = agibotdds.Node("subscriber")
    test_node.create_subscriber(
        "topic/test1", TestMeta, qos, callback)
    test_node.spin()

if __name__ == '__main__':
    agibotdds.init("subscriber")
    test_subscriber_class()
    agibotdds.shutdown()
