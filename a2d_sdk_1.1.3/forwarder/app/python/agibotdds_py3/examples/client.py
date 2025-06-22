#!/usr/bin/env python3

import time
from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.sample_pb2 import SampleMessage


def test_client_class():
    """
    Client send request.
    """
    print("=" * 120)
    test_node = agibotdds.Node("client_node")
    client = test_node.create_client(
        "agibotdds_py3/sample_cs", SampleMessage, SampleMessage)
    req = SampleMessage()
    req.id = 0
    count = 0
    while not agibotdds.is_shutdown():
        time.sleep(1)
        req.id = count
        print("-" * 80)
        response = client.send_request(req)
        print("get Response from request No [ ", count, "] : ", response)
        count += 1


if __name__ == '__main__':
    agibotdds.init("client")
    test_client_class()
    agibotdds.shutdown()
