#!/usr/bin/env python3

from agibotdds_py3 import agibotdds
from agibotdds_py3.examples.agibotdds_test_pub_serv_messages_pb2 import AppReq, AppStatus

num = 1
seq = 0

def callback(req):
    """
    service message callback.
    """
    global seq
    global num
    print(f"Request {num} {req.req_num}, res {seq}")

    req_num = req.req_num
    res = AppStatus()
    res.name = "000000"
    res.process = str(num)
    res.timestamp = 0
    res.pid = seq
    res.last_heartbeat = 0
    res.interval = req_num
    seq += 1
    return res


def test_service_class():
    """
    Service message.
    """
    test_node = agibotdds.Node("service_node" + str(num))
    test_node.create_service(
        "topic/test_service" + str(num), AppReq, AppStatus, callback)
    test_node.spin()


if __name__ == '__main__':
    agibotdds.init("service")
    test_service_class()
    agibotdds.shutdown()
