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
Module test_csvdb
"""

import pytest

from smartwatts.report_model import HWPCModel, KEYS_COMMON
from smartwatts.database import CsvDB
from smartwatts.database import CsvBadFilePathError, CsvBadCommonKeys

PATH_TO_TEST = "./smartwatts/test/environment/csv/"

# All this file raise error
BAD_COMMON = [PATH_TO_TEST + "bad_common_miss_sensor.csv",
              PATH_TO_TEST + "bad_common_miss_target.csv",
              PATH_TO_TEST + "bad_common_miss_timestamp.csv"]

# Create 2 full HWPCReport
BASIC_FILES = [PATH_TO_TEST + "core2.csv",
               PATH_TO_TEST + "rapl2.csv",
               PATH_TO_TEST + "pcu2.csv"]

# Create 1 full HWPCReport (first miss)
FIRST_PRIMARY_MISSING = [PATH_TO_TEST + "core1_miss_first.csv",
                         PATH_TO_TEST + "rapl2.csv",
                         PATH_TO_TEST + "pcu2.csv"]

# Create 1 full HWPCReport (second miss)
SECOND_PRIMARY_MISSING = [PATH_TO_TEST + "core1_miss_second.csv",
                          PATH_TO_TEST + "rapl2.csv",
                          PATH_TO_TEST + "pcu2.csv"]

# Create 2 HWPCReport, first without rapl, second full
FIRST_RAPL_MISSING = [PATH_TO_TEST + "core2.csv",
                      PATH_TO_TEST + "rapl1_miss_first.csv",
                      PATH_TO_TEST + "pcu2.csv"]

# Create 2 HWPCReport, first full, second without rapl
SECOND_RAPL_MISSING = [PATH_TO_TEST + "core2.csv",
                       PATH_TO_TEST + "rapl1_miss_second.csv",
                       PATH_TO_TEST + "pcu2.csv"]


class TestCsvDB():
    """
    Test class of CsvDB class
    """

    def test_csvdb_bad_filepath(self):
        """
        Test with bad filepath
        """
        with pytest.raises(CsvBadFilePathError) as pytest_wrapped:
            CsvDB(HWPCModel(), ["/tmp/unknowfile"]).load()
        assert pytest_wrapped.type == CsvBadFilePathError

    def test_csvdb_bad_common(self):
        """
        Test when file miss some common column
        """
        csv_files = BAD_COMMON
        while csv_files:
            with pytest.raises(CsvBadCommonKeys) as pytest_wrapped:
                CsvDB(HWPCModel(), csv_files).load()
            assert pytest_wrapped.type == CsvBadCommonKeys
            csv_files = csv_files[1:]

    def test_csvdb_two_reports(self):
        """
        Create two full HWPCReport, then return None
        """
        csvdb = CsvDB(HWPCModel(), BASIC_FILES)
        csvdb.load()
        group_name = [path.split('/')[-1] for path in BASIC_FILES]

        for _ in range(2):
            report = csvdb.get_next()
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                assert group in report['groups']
        assert csvdb.get_next() is None

    def test_csvdb_first_primary_missing(self):
        """
        Create one full HWPCReport (the second), then return None
        """
        csvdb = CsvDB(HWPCModel(), FIRST_PRIMARY_MISSING)
        csvdb.load()
        group_name = [path.split('/')[-1] for path in FIRST_PRIMARY_MISSING]

        report = csvdb.get_next()
        for key in KEYS_COMMON:
            assert key in report
        for group in group_name:
            assert group in report['groups']
        assert report['timestamp'] == "1539260665189"
        assert csvdb.get_next() is None

    def test_csvdb_second_primary_missing(self):
        """
        Create one full HWPCReport (the first), then return None
        """
        csvdb = CsvDB(HWPCModel(), SECOND_PRIMARY_MISSING)
        csvdb.load()
        group_name = [path.split('/')[-1] for path in SECOND_PRIMARY_MISSING]

        report = csvdb.get_next()
        for key in KEYS_COMMON:
            assert key in report
        for group in group_name:
            assert group in report['groups']
        assert report['timestamp'] == "1539260664189"
        assert csvdb.get_next() is None

    def test_csvdb_first_rapl_missing(self):
        """
        Create two reports, one without rapl, second is full, then return None
        """
        csvdb = CsvDB(HWPCModel(), FIRST_RAPL_MISSING)
        csvdb.load()
        group_name = [path.split('/')[-1] for path in FIRST_RAPL_MISSING]

        for i in range(2):
            report = csvdb.get_next()
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                if i == 0 and "rapl" in group:
                    assert group not in report['groups']
                else:
                    assert group in report['groups']
        assert csvdb.get_next() is None


    def test_csvdb_second_rapl_missing(self):
        """
        Create two reports, one is full, second without rapl, then return None
        """
        csvdb = CsvDB(HWPCModel(), SECOND_RAPL_MISSING)
        csvdb.load()
        group_name = [path.split('/')[-1] for path in SECOND_RAPL_MISSING]

        for i in range(2):
            report = csvdb.get_next()
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                if i == 1 and "rapl" in group:
                    assert group not in report['groups']
                else:
                    assert group in report['groups']
        assert csvdb.get_next() is None
