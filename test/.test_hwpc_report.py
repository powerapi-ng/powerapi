# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module test_hwpc_report
"""

import pytest
from smartwatts.filter import HWPCFilter, FilterUselessError
from smartwatts.report import HWPCReport, HWPCReportSocket, HWPCReportCore
from smartwatts.report import create_core_report, create_socket_report
from smartwatts.report_model import HWPCModel
from smartwatts.database import MongoDB


CORE_ID1 = 3
CORE_ID2 = 3
EVENT1 = {'toto': 123}
EVENT2 = {'event2': 456}
FULL_EVENT = {}
FULL_EVENT.update(EVENT1)
FULL_EVENT.update(EVENT2)

SOCKET_ID = 4

class TestHWPCReport:
    """ Class TestHWPCReport """

    def test_report_core(self):
        """ Test basic report core """
        report_core = create_core_report(CORE_ID1, EVENT1[0], EVENT1[1])
        assert report_core.serialize() == EVENT1
        report_core.deserialize(EVENT2)
        assert report_core.events == FULL_EVENT
        assert report_core.core_id == CORE_ID1

    def test_report_socket(self):
        report_core1 = create_core_report(CORE_ID1, None, None, FULL_EVENT)
        report_core2 = create_core_report(CORE_ID2, None, None, FULL_EVENT)
        report_socket = create_socket_report(4, [report_core1, report_core2])

    def test_report(self):
        pass
