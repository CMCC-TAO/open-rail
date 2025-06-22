#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""Module for init environment."""

import ctypes
import importlib
import os
import sys
import threading
import time

from enum import unique, Enum
from google.protobuf.descriptor_pb2 import FileDescriptorProto


PY_CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)
PY_CALLBACK_TYPE_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)

##
# init vars for integration docker env.

_AGIBOTDDS = importlib.import_module('cosine_bus.lib.libpy_agibotdds')

##
# @brief init agibotdds environment.
# @param module_name Used as the log file name.
#
# @return Success is True, otherwise False.


def init(module_name="agibotdds_py"):
    """
    init agibotdds environment.
    """
    return _AGIBOTDDS.py_init(module_name)


def ok():
    """
    is agibotdds envi ok.
    """
    return _AGIBOTDDS.py_ok()


def shutdown():
    """
    shutdown agibotdds envi.
    """
    return _AGIBOTDDS.py_shutdown()


def is_shutdown():
    """
    is agibotdds shutdown.
    """
    return _AGIBOTDDS.py_is_shutdown()


def waitforshutdown():
    """
    wait until the agibotdds is shutdown.
    """
    return _AGIBOTDDS.py_waitforshutdown()


# //////////////////////////////class//////////////////////////////


class Publisher(object):

    """
    Class for agibotdds publisher wrapper.
    """

    def __init__(self, name, publisher, data_type, qos):
        self.name = name
        self.publisher = publisher
        self.data_type = data_type
        self.qos = qos

    ##
    # @brief publish message.
    #
    # @param data is a message type.
    #
    # @return Success is 0, otherwise False.
    def publish(self, data):
        """
        publisher message string
        """
        return _AGIBOTDDS.PyPublisher_publish(self.publisher, data.SerializeToString())


class Subscriber(object):

    """
    Class for agibotdds subscriber wrapper.
    """

    def __init__(self, name, subscriber, data_type, qos):
        self.name = name
        self.subscriber = subscriber
        self.data_type = data_type
        self.qos = qos

    def read_frame_nearest(self, timestamp_ns):
        """
        Read the frame nearest to the given timestamp.
        
        Args:
            timestamp_ns: timestamp in nanoseconds
            
        Returns:
            The nearest message if found, None otherwise
        """
        msg_str = _AGIBOTDDS.PySubscriber_read_frame_nearest(self.subscriber, timestamp_ns)
        if msg_str and len(msg_str) > 0:
            proto = self.data_type()
            proto.ParseFromString(msg_str)
            return proto
        return None


class Client(object):

    """
    Class for agibotdds service client wrapper.
    """

    def __init__(self, client, data_type):
        self.client = client
        self.data_type = data_type

    ##
    # @brief send request message to service.
    #
    # @param data is a message type.
    #
    # @return None or response from service.
    def send_request(self, data):
        """
        send request to service
        """
        response_str = _AGIBOTDDS.PyClient_send_request(
            self.client, data.SerializeToString())
        if len(response_str) == 0:
            return None

        response = self.data_type()
        response.ParseFromString(response_str)
        return response

class qos(object):

    """
    Class for agibotdds qos wrapper.
    Members:
        history: must be a value of:
            qos.History.KEEP_LAST
            qos.History.KEEP_ALL
        depth: must be an [int] value
        reliability: must be a value of:
            qos.Reliability.BEST_EFFORT
            qos.Reliability.RELIABLE
        durability: must be a value of:
            qos.Durability.VOLATILE
            qos.Durability.TRANSIENT_LOCAL
    """

    @unique
    class History(Enum):
        KEEP_LAST = 0
        KEEP_ALL = 1

    @unique
    class Reliability(Enum):
        BEST_EFFORT = 0
        RELIABLE = 1

    @unique
    class Durability(Enum):
        VOLATILE = 0
        TRANSIENT_LOCAL = 1

    def __init__(self, history=History.KEEP_LAST, depth=5, reliability=Reliability.RELIABLE, durability=Durability.VOLATILE):
        if not isinstance(history, self.History):
            raise ValueError("qos history must be [qos.History] type!")
        if not isinstance(depth, int):
            raise ValueError("qos depth must be [int] type!")
        if not isinstance(reliability, self.Reliability):
            raise ValueError("qos reliability must be [qos.Reliability] type!")
        if not isinstance(durability, self.Durability):
            raise ValueError("qos durability must be [qos.Durability] type!")
        self.history = history
        self.depth = depth
        self.reliability = reliability
        self.durability = durability
        self.QoS = _AGIBOTDDS.new_PyQoS(
            history.value, depth, reliability.value, durability.value)

    def __del__(self):
        _AGIBOTDDS.delete_PyQoS(self.QoS)


class Node(object):

    """
    Class for agibotdds Node wrapper.
    """

    def __init__(self, name):
        self.node = _AGIBOTDDS.new_PyNode(name)
        self.list_publisher = []
        self.list_subscriber = []
        self.subs = {}
        self.pubs = {}
        self.list_client = []
        self.list_service = []
        self.mutex = threading.Lock()
        self.callbacks = {}
        self.services = {}

    def __del__(self):
        for publisher in self.list_publisher:
            _AGIBOTDDS.delete_PyPublisher(publisher)
        for subscriber in self.list_subscriber:
            _AGIBOTDDS.delete_PySubscriber(subscriber)
        for c in self.list_client:
            _AGIBOTDDS.delete_PyClient(c)
        for s in self.list_service:
            _AGIBOTDDS.delete_PyService(s)
        _AGIBOTDDS.delete_PyNode(self.node)

    ##
    # @brief register proto message by proto descriptor file.
    #
    # @param file_desc object about datatype.DESCRIPTOR.file .
    def register_message(self, file_desc):
        """
        register proto message desc file.
        """
        for dep in file_desc.dependencies:
            self.register_message(dep)
        proto = FileDescriptorProto()
        file_desc.CopyToProto(proto)
        proto.name = file_desc.name
        desc_str = proto.SerializeToString()
        _AGIBOTDDS.PyNode_register_message(self.node, desc_str)

    ##
    # @brief create a channel publisher for send message to another channel.
    #
    # @param name is the channel name.
    # @param data_type is message class for serialization
    # @param qos is the QoS settings.
    #
    # @return return the publisher object.
    def create_publisher(self, name, data_type, qos):
        """
        create a channel publisher for send message to another channel.
        """
        self.register_message(data_type.DESCRIPTOR.file)
        datatype = data_type.DESCRIPTOR.full_name
        publisher = _AGIBOTDDS.PyNode_create_publisher(self.node, name,
                                                    datatype, qos.QoS)
        self.list_publisher.append(publisher)
        return Publisher(name, publisher, datatype, qos)

    def subscriber_callback(self, name):
        sub = self.subs[name.decode('utf8')] #(subscriber, callback, args, data_type, qos, False)
        msg_str = _AGIBOTDDS.PySubscriber_subscribe(sub[0], False)
        if msg_str and len(msg_str) > 0:
            if sub[3] is None:
                proto = msg_str
            else:
                proto = sub[3]()
                proto.ParseFromString(msg_str)
            if sub[2] is None:
                sub[1](proto)
            else:
                sub[1](proto, sub[2])
        return 0

    ##
    # @brief create a channel subscriber for receive message from another channel.
    #
    # @param name the channel name to subscribe.
    # @param data_type  message class for serialization
    # @param qos is the QoS settings.
    # @param callback function to call (fn(data)) when data is received. If
    # args is set, the function must accept the args as a second argument,
    # i.e. fn(data, args)
    # @param args additional arguments to pass to the callback
    # @param raw when set true, raw bytes will be pass to callback without deserialize the message
    #
    # @return return the publisher object.
    def create_subscriber(self, name, data_type, qos, callback, args=None, raw=False):
        """
        create a channel subscriber for receive message from another channel.
        """
        self.mutex.acquire()
        if name in self.subs.keys():
            self.mutex.release()
            return None
        self.mutex.release()

        self.register_message(data_type.DESCRIPTOR.file)
        datatype = data_type.DESCRIPTOR.full_name

        subscriber = _AGIBOTDDS.PyNode_create_subscriber(
            self.node, name, datatype, qos.QoS)
        if subscriber is None:
            return None
        self.list_subscriber.append(subscriber)

        if raw:
            sub = (subscriber, callback, args, None, qos, False)
        else:
            sub = (subscriber, callback, args, data_type, qos, False)

        self.mutex.acquire()
        self.subs[name] = sub
        self.mutex.release()
        fun_subscriber_cb = PY_CALLBACK_TYPE(self.subscriber_callback)
        self.callbacks[name] = fun_subscriber_cb
        f_ptr = ctypes.cast(self.callbacks[name], ctypes.c_void_p).value
        _AGIBOTDDS.PySubscriber_register_func(subscriber, f_ptr)

        return Subscriber(name, subscriber, data_type, qos)

        ##
    # @brief create client for the c/s.
    #
    # @param name the service name.
    # @param request_data_type the request message type.
    # @param response_data_type the response message type.
    #
    # @return the client object.
    def create_client(self, name, request_data_type, response_data_type):
        datatype = request_data_type.DESCRIPTOR.full_name
        c = _AGIBOTDDS.PyNode_create_client(self.node, name,
                                        str(datatype))
        self.list_client.append(c)
        return Client(c, response_data_type)

    def service_callback(self, name):
        v = self.services[name.decode('utf8')]
        msg_str = _AGIBOTDDS.PyService_read(v[0])
        if (len(msg_str) > 0):
            proto = v[3]()
            proto.ParseFromString(msg_str)
            response = None
            if v[2] is None:
                response = v[1](proto)
            else:
                response = v[1](proto, v[2])
            _AGIBOTDDS.PyService_write(v[0], response.SerializeToString())
        return 0

    ##
    # @brief create service for the c/s.
    #
    # @param name the service name.
    # @param req_data_type the request message type.
    # @param res_data_type the response message type.
    # @param callback function to call (fn(data)) when data is received. If
    # args is set, the function must accept the args as a second argument,
    # i.e. fn(data, args)
    # @param args additional arguments to pass to the callback.
    #
    # @return return the service object.
    def create_service(self, name, req_data_type, res_data_type, callback,
                       args=None):
        self.mutex.acquire()
        if name in self.services.keys():
            self.mutex.release()
            return None
        self.mutex.release()
        datatype = req_data_type.DESCRIPTOR.full_name
        s = _AGIBOTDDS.PyNode_create_service(self.node, name, str(datatype))
        self.list_service.append(s)
        v = (s, callback, args, req_data_type, False)
        self.mutex.acquire()
        self.services[name] = v
        self.mutex.release()
        f = PY_CALLBACK_TYPE(self.service_callback)
        self.callbacks[name] = f
        f_ptr = ctypes.cast(f, ctypes.c_void_p).value
        _AGIBOTDDS.PyService_register_func(s, f_ptr)
        return s

    ##
    # @brief Get the communication topo
    # @return String of topo in json format
    ##
    def get_topo(self) -> str:
        return _AGIBOTDDS.PyNode_get_topo(self.node)

    def spin(self):
        """
        spin for every 0.002s.
        """
        while not _AGIBOTDDS.py_is_shutdown():
            time.sleep(0.002)


@unique
class Preceision(Enum):
    Seconds = 0
    Milliseconds = 1
    Microseconds = 2
    Nanoseconds = 3


@unique
class TimeSource(Enum):
    PTP = 0
    System = 1


class Time(object):
    @staticmethod
    def ptp(pre: Preceision = Preceision.Milliseconds):
        ##
        # @brief Get the PTP timestamp.
        # @param preceision The precesion of the time, Seconds/Milliseconds/Microseconds/Nanoseconds, default is Milliseconds
        # @return Elasped time since power on.
        ##
        if not isinstance(pre, Preceision):
            raise ValueError("time preceision must be [Preceision] type!")
        return _AGIBOTDDS.PyTime_ptp(pre.value)

    @staticmethod
    def utc(pre: Preceision = Preceision.Milliseconds):
        ##
        # @brief Get the UTC timestamp.
        # @param preceision The precesion of the time, Seconds/Milliseconds/Microseconds/Nanoseconds, default is Milliseconds
        # @return Elasped time since 1970-1-1.
        ##
        if not isinstance(pre, Preceision):
            raise ValueError("time preceision must be [Preceision] type!")
        return _AGIBOTDDS.PyTime_utc(pre.value)

    @staticmethod
    def sleep(dur: int, pre: Preceision = Preceision.Milliseconds):
        ##
        # @brief Make the current thread sleep in ms.
        # @param duration_ms Duration to sleep, in ms, if the value of this param is 0, means sleep for minimal possilbe period (1ns).
        # @param preceision The unit of the sleep time, Seconds/Milliseconds/Microseconds/Nanoseconds, default is Milliseconds
        ##
        if not isinstance(pre, Preceision):
            raise ValueError("time preceision must be [Preceision] type!")
        _AGIBOTDDS.PyTime_sleep(dur, pre.value)

    @staticmethod
    def enable_virtual_mode(base_time: int = 0):
        ##
        # @brief Set Time to virtual mode, means the time returned from Time::Utc() or Time::Ptp is not real utc/ptp time.
        # @param base_time This is a timestamp in nanoseconds represents the time to simulate, default is 0, means that user can set the current time manually by calling SetVirtualTime(ts)
        ##
        _AGIBOTDDS.PyTime_enable_virtual_mode(base_time)

    @staticmethod
    def disable_virtual_mode():
        ##
        # @brief Set Time to real mode.
        ##
        _AGIBOTDDS.PyTime_disable_virtual_mode()

    @staticmethod
    def is_in_virtual_mode() -> bool:
        ##
        # @brief Determine if Time is in virtual mode.
        # @return Return true if Time has been set in virtual mode.
        ##
        return _AGIBOTDDS.PyTime_is_in_virtual_mode()

    @staticmethod
    def set_virtual_time(timestamp: int):
        ##
        # @brief Set the current time manually.
        # @param timestamp This is a timestamp in nanoseconds to be set as the return value of Time::Utc() or Time::Ptp()
        ##
        _AGIBOTDDS.PyTime_set_virtual_time(timestamp)

    @staticmethod
    def get_virtual_time(pre: Preceision, src: TimeSource):
        ##
        # @brief Set the current time manually.
        # @param timestamp This is a timestamp in nanoseconds to be set as the return value of Time::Utc() or Time::Ptp()
        ##
        if not isinstance(pre, Preceision):
            raise ValueError("time preceision must be [Preceision] type!")
        if not isinstance(src, TimeSource):
            raise ValueError("time source must be [TimeSource] type!")
        return _AGIBOTDDS.PyTime_get_virtual_time(pre.value, src.value)

    @staticmethod
    def get_real_time(pre: Preceision, src: TimeSource):
        ##
        # @brief Set the current time manually.
        # @param timestamp This is a timestamp in nanoseconds to be set as the return value of Time::Utc() or Time::Ptp()
        ##
        if not isinstance(pre, Preceision):
            raise ValueError("time preceision must be [Preceision] type!")
        if not isinstance(src, TimeSource):
            raise ValueError("time source must be [TimeSource] type!")
        return _AGIBOTDDS.PyTime_get_real_time(pre.value, src.value)
