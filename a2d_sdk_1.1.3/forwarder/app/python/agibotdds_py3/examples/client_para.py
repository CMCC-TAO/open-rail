#!/usr/bin/env python3

import time
from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.agibotdds_test_pub_serv_messages_pb2 import AppReq, AppStatus


def test_client_class():
    """
    Client send request.
    """
    print("=" * 120)
    num = 1
    seq = 0
    interval = 20
    test_node = agibotdds.Node("client" + str(num))
    client = test_node.create_client(
        "topic/test_service" + str(num), AppReq, AppStatus)
    req = AppReq()
    while not agibotdds.is_shutdown():
        time.sleep(interval / 1000)
        req.req_num = seq
        print("-" * 80)
        response = client.send_request(req)
        if response:
            print(f"Response {response.process} req {seq} : res: {response.interval}")
        seq += 1


if __name__ == '__main__':
    agibotdds.init("client")
    test_client_class()
    agibotdds.shutdown()
