#!/usr/bin/env python3

from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.sample_pb2 import SampleMessage


def callback(data):
    """
    service message callback.
    """
    print("-" * 80)
    print("get Request [ ", data, " ]")
    return SampleMessage(id=data.id)


def test_service_class():
    """
    Service message.
    """
    print("=" * 120)
    test_node = agibotdds.Node("service_node")
    test_node.create_service(
        "agibotdds_py3/sample_cs", SampleMessage, SampleMessage, callback)
    test_node.spin()


if __name__ == '__main__':
    agibotdds.init("service")
    test_service_class()
    agibotdds.shutdown()
