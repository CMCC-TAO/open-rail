#!/usr/bin/env python3

from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.sample_pb2 import SampleMessage


def callback(data):
    """
    Subscriber message callback.
    """
    print("=" * 80)
    print("subscriber callback msg->:")
    print(data)


def test_subscriber_class():
    """
    Subscriber message.
    """
    print("=" * 120)
    # default QoS
    qos = agibotdds.qos()
    test_node = agibotdds.Node("subscriber")
    test_node.create_subscriber(
        "agibotdds_py3/sample", SampleMessage, qos, callback)
    test_node.spin()


if __name__ == '__main__':
    agibotdds.init("subscriber")
    test_subscriber_class()
    agibotdds.shutdown()
