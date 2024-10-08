#!/usr/bin/env python3

"""
Created on 27 Aug 2019

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

from scs_core.data.queue_report import QueueReport, ClientStatus
from scs_core.psu.psu_conf import PSUConf

from scs_host.sys.host import Host


# --------------------------------------------------------------------------------------------------------------------

filename = PSUConf.report_file(Host)

report = QueueReport(23, ClientStatus.CONNECTED, True)
print(report)
print(report.as_json())

report.save(filename)
print("-")

report = QueueReport.load(filename)
print(report)

