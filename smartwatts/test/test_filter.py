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
Module test_filter
"""

import pytest
from smartwatts.filter import HWPCFilter, FilterUselessError
from smartwatts.report import HWPCReport
from smartwatts.report_model import HWPCModel
from smartwatts.database import MongoDB


class TestFilter:

    def test_without_filter(self):
        """ Test filter without any filter, raise an error """
        hwpc_filter = HWPCFilter()
        with pytest.raises(FilterUselessError) as pytest_wrapped:
            hwpc_filter.route(HWPCReport())
        assert pytest_wrapped.type == FilterUselessError


    def test_with_two_filter(self):
        """
        Test filter with two filter
        - 2 first report return first dispatcher
        - 2 next report return second dispatcher
        - 2 next report return None
        """
        mongodb = MongoDB("localhost", 27017, "test_filter",
                          "test_filter1", report_model=HWPCModel())
        mongodb.load()
        hwpc_filter = HWPCFilter()
        hwpc_filter.filter(lambda msg:
                           True if msg.sensor == "sensor_test1" else False,
                           1)
        hwpc_filter.filter(lambda msg:
                           True if msg.sensor == "sensor_test2" else False,
                           2)
        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) == 1

        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) == 2

        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) is None
