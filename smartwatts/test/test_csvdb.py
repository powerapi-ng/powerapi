"""
Module test_csvdb
"""

import pytest

from smartwatts.report_model import HWPCModel
from smartwatts.database import CsvDB
from smartwatts.database import CsvBadFilePathError, CsvBadCommonKeys

PATH_TO_TEST = "./smartwatts/test/"
BAD_COMMON = [PATH_TO_TEST + "data_test/bad_common_miss_sensor.csv",
              PATH_TO_TEST + "data_test/bad_common_miss_target.csv",
              PATH_TO_TEST + "data_test/bad_common_miss_timestamp.csv"]


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
