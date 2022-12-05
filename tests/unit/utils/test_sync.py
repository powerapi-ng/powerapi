# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest
from powerapi.utils.sync import Sync
from powerapi.report import Report, ProcfsReport, PowerReport
from powerapi.test_utils.reports import power_timeline, procfs_timeline
import datetime


class Report1(Report):
    """
    Type 1 of report
    """


class Report2(Report):
    """
    Type 2 of report
    """


def type1(t):
    """ Identificator of type1"""
    return type(t) == Report1


def type2(t):
    """ Identificator of type2"""
    return type(t) == Report2


def test_request_while_no_pair_available_return_None():
    timestamp = datetime.date(1970, 1, 1)
    timedet = datetime.timedelta(1)

    sync = Sync(type1, type2, timedet)

    sync.add_report(Report1(timestamp, "", ""))
    sync.add_report(Report1(timestamp + timedet, "", ""))
    sync.add_report(Report1(timestamp + 2 * timedet, "", ""))
    sync.add_report(Report1(timestamp + 3 * timedet, "", ""))

    assert sync.request() is None


def test_request_while_report_missing_return_correct_data():
    timestamp = datetime.date(1970, 1, 1)
    timedet = datetime.timedelta(1)
    delay = datetime.timedelta(1)

    sync = Sync(type1, type2, delay)

    sync.add_report(Report1(timestamp, "", ""))
    sync.add_report(Report1(timestamp + timedet, "", ""))
    sync.add_report(Report1(timestamp + 2 * timedet, "", ""))
    sync.add_report(Report1(timestamp + 3 * timedet, "", ""))
    sync.add_report(Report2(timestamp + 3 * timedet, "", ""))

    (report1, report2) = sync.request()

    assert report1.timestamp == (timestamp + 2 * timedet)
    assert report2.timestamp == (timestamp + 3 * timedet)


def test_request_correct_use_return_correct_data():
    timestamp = datetime.date(1970, 1, 1)
    timedet = datetime.timedelta(1)
    sync = Sync(type1, type2, timedet)

    sync.add_report(Report1(timestamp, "", ""))
    for t in range(100):
        sync.add_report(Report1(timestamp + (t + 1) * timedet, "", ""))
        sync.add_report(Report2(timestamp + t * timedet, "", ""))

    r = sync.request()
    while r is not None:
        report1, report2 = r
        assert abs(report1.timestamp - report2.timestamp) <= timedet
        r = sync.request()


def test_send_timeline_of_reports_receive_right_pair(procfs_timeline, power_timeline):
    timedet = datetime.timedelta(250)
    sync = Sync(lambda x: isinstance(x, PowerReport),
                lambda x: isinstance(x, ProcfsReport),
                timedet)

    sum = 0

    r = power_timeline[0]
    sync.add_report(PowerReport.from_json(r))
    r = power_timeline[1]
    sync.add_report(PowerReport.from_json(r))

    for i in range(len(power_timeline) - 2):
        r = power_timeline[i + 2]
        sync.add_report(PowerReport.from_json(r))

        r = procfs_timeline[i]
        sync.add_report(ProcfsReport.from_json(r))

        r = sync.request()
        assert r is not None
        report1, report2 = r
        assert abs(report1.timestamp - report2.timestamp) <= timedet
        sum += 1

    r = procfs_timeline[-2]
    sync.add_report(ProcfsReport.from_json(r))

    r = procfs_timeline[-1]
    sync.add_report(ProcfsReport.from_json(r))

    assert sum == len(power_timeline) - 2


def test_send_report_in_special_order_receive_right_pair(procfs_timeline, power_timeline):
    timedet = datetime.timedelta(250)
    sync = Sync(lambda x: isinstance(x, PowerReport),
                lambda x: isinstance(x, ProcfsReport),
                timedet)

    sum = 0

    r = power_timeline[0]
    sync.add_report(PowerReport.from_json(r))
    r = power_timeline[1]
    sync.add_report(PowerReport.from_json(r))

    for i in range(len(power_timeline) - 2):
        r = power_timeline[i + 2]
        sync.add_report(PowerReport.from_json(r))

        r = procfs_timeline[i]
        sync.add_report(ProcfsReport.from_json(r))

        r = sync.request()
        assert r is not None
        report1, report2 = r
        assert abs(report1.timestamp - report2.timestamp) <= timedet
        sum += 1

    r = procfs_timeline[-2]
    sync.add_report(ProcfsReport.from_json(r))

    r = procfs_timeline[-1]
    sync.add_report(ProcfsReport.from_json(r))

    assert sum == len(power_timeline) - 2
