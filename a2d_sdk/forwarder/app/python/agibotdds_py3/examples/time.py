#!/usr/bin/env python3

from agibotdds_py3 import agibotdds


if __name__ == '__main__':
    print("time ptp:", agibotdds.Time.ptp(agibotdds.Preceision.Nanoseconds))
    agibotdds.Time.sleep(5, agibotdds.Preceision.Seconds)
    print("time ptp:", agibotdds.Time.ptp(agibotdds.Preceision.Nanoseconds))

    ##
    print("time utc:", agibotdds.Time.utc(agibotdds.Preceision.Microseconds))
    agibotdds.Time.sleep(500, agibotdds.Preceision.Milliseconds)
    print("time utc:", agibotdds.Time.utc())

    ##
    print("is in virtual mode?", agibotdds.Time.is_in_virtual_mode())

    ##
    print("get virtual time ptp?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get virtual time utc?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

    print("get real time ptp?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get real time utc?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

    ##
    print("enable virtual mode")
    agibotdds.Time.enable_virtual_mode()
    print("is in virtual mode?", agibotdds.Time.is_in_virtual_mode())

    ##
    print("set virtual time:1666316428012378880")
    agibotdds.Time.set_virtual_time(1666316428012378880)
    print("time ptp:", agibotdds.Time.ptp(agibotdds.Preceision.Nanoseconds))
    print("time utc:", agibotdds.Time.utc(agibotdds.Preceision.Nanoseconds))

    print("get virtual time ptp?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get virtual time utc?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

    print("get real time ptp?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get real time utc?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

    ##
    print("disable virtual mode")
    agibotdds.Time.disable_virtual_mode()
    print("is in virtual mode?", agibotdds.Time.is_in_virtual_mode())

    print("get virtual time ptp?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get virtual time utc?", agibotdds.Time.get_virtual_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

    print("get real time ptp?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.PTP))
    print("get real time utc?", agibotdds.Time.get_real_time(agibotdds.Preceision.Nanoseconds, agibotdds.TimeSource.System))

