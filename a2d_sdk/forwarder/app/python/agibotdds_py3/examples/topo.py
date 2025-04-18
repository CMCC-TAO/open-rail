#!/usr/bin/env python3

from agibotdds_py3 import agibotdds


def test_topo_class():
    """
    Print topo
    """
    test_node = agibotdds.Node("topo_node")
    print("The communication topo: \n\n", test_node.get_topo())

if __name__ == '__main__':
    agibotdds.init("topo")
    test_topo_class()
    agibotdds.shutdown()
