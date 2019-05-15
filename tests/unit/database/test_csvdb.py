"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pytest
import shutil
import os
import csv

from powerapi.report import HWPCReport, create_core_report, create_group_report, create_report_root,\
    create_socket_report
from powerapi.report import PowerReport
from powerapi.report_model import PowerModel, HWPCModel, KEYS_COMMON
from powerapi.database import CsvDB
from powerapi.database import CsvBadFilePathError, CsvBadCommonKeysError, HeaderAreNotTheSameError

PATH_TO_TEST = "./tests/unit/environment/csv/"

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


######### For CsvDB saving

# Cpt
CPT = 1

# Path where save files
PATH_TO_SAVE = "/tmp/csvdb_test/"

# Sensor and target
SENSOR = "sensor"
TARGET = "target"


###################
# Report Creation #
###################

def gen_good_report():
    """
    Return a well formated HWPCReport
    """
    cpua = create_core_report('1', 'e0', '0')
    cpub = create_core_report('2', 'e0', '1')
    cpuc = create_core_report('1', 'e0', '2')
    cpud = create_core_report('2', 'e0', '3')
    cpue = create_core_report('1', 'e1', '0')
    cpuf = create_core_report('2', 'e1', '1')
    cpug = create_core_report('1', 'e1', '2')
    cpuh = create_core_report('2', 'e1', '3')

    socketa = create_socket_report('1', [cpua, cpub])
    socketb = create_socket_report('2', [cpuc, cpud])
    socketc = create_socket_report('1', [cpue, cpuf])
    socketd = create_socket_report('2', [cpug, cpuh])

    groupa = create_group_report('1', [socketa, socketb])
    groupb = create_group_report('2', [socketc, socketd])

    return create_report_root([groupa, groupb])


def gen_power_report():
    global CPT
    CPT += 1
    return PowerReport(CPT, SENSOR, TARGET, 0.11, {"metadata1": "truc", "metadata2": "oui"})

##################
#    FIXTURES    #
##################

@pytest.fixture
def clean_csv_files():
    """
    setup: remove repository in current path
    """
    shutil.rmtree(PATH_TO_SAVE, ignore_errors=True)
    yield


@pytest.fixture()
def corrupted_csvdb():
    """
    Create a corrupted csvdb file
    """
    full_path = PATH_TO_SAVE + SENSOR + "-" + TARGET + "/"
    try:
        os.makedirs(full_path)
    except FileExistsError:
        pass

    with open(full_path + "PowerReport.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, ["fake_field", "fake_field2"])
        writer.writeheader()
        writer.writerow({"fake_field": "One", "fake_field2": "Two"})
        csvfile.close()


##################
#     TESTS      #
##################

class TestCsvDB():
    """
    Test class of CsvDB class
    """

    def test_csvdb_bad_filepath(self):
        """
        Test with bad filepath
        """
        with pytest.raises(CsvBadFilePathError) as pytest_wrapped:
            CsvDB(HWPCModel(), files_name=["/tmp/unknowfile"]).connect()
        assert pytest_wrapped.type == CsvBadFilePathError

    def test_csvdb_bad_common(self):
        """
        Test when file miss some common column
        """
        csv_files = BAD_COMMON
        while csv_files:
            with pytest.raises(CsvBadCommonKeysError) as pytest_wrapped:
                CsvDB(HWPCModel(), files_name=csv_files).connect()
            assert pytest_wrapped.type == CsvBadCommonKeysError
            csv_files = csv_files[1:]

    def test_csvdb_two_reports(self):
        """
        Create two full HWPCReport, then return None
        """
        csvdb = CsvDB(HWPCModel(), files_name=BASIC_FILES)
        csvdb.connect()
        group_name = [path.split('/')[-1] for path in BASIC_FILES]

        csvdb_iter = iter(csvdb)
        for _ in range(2):
            report = next(csvdb_iter)
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                assert group in report['groups']

        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_iter)
        assert pytest_wrapped.type == StopIteration

    def test_csvdb_first_primary_missing(self):
        """
        Create one full HWPCReport (the second), then return None
        """
        csvdb = CsvDB(HWPCModel(), files_name=FIRST_PRIMARY_MISSING)
        csvdb.connect()
        group_name = [path.split('/')[-1] for path in FIRST_PRIMARY_MISSING]

        csvdb_iter = iter(csvdb)
        report = next(csvdb_iter)
        for key in KEYS_COMMON:
            assert key in report
        for group in group_name:
            assert group in report['groups']
        assert report['timestamp'] == "1539260665189"
        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_iter)
        assert pytest_wrapped.type == StopIteration

    def test_csvdb_second_primary_missing(self):
        """
        Create one full HWPCReport (the first), then return None
        """
        csvdb = CsvDB(HWPCModel(), files_name=SECOND_PRIMARY_MISSING)
        csvdb.connect()
        group_name = [path.split('/')[-1] for path in SECOND_PRIMARY_MISSING]

        csvdb_iter = iter(csvdb)
        report = next(csvdb_iter)
        for key in KEYS_COMMON:
            assert key in report
        for group in group_name:
            assert group in report['groups']
        assert report['timestamp'] == "1539260664189"
        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_iter)
        assert pytest_wrapped.type == StopIteration

    def test_csvdb_first_rapl_missing(self):
        """
        Create two reports, one without rapl, second is full, then return None
        """
        csvdb = CsvDB(HWPCModel(), files_name=FIRST_RAPL_MISSING)
        csvdb.connect()
        group_name = [path.split('/')[-1] for path in FIRST_RAPL_MISSING]

        csvdb_iter = iter(csvdb)
        for i in range(2):
            report = next(csvdb_iter)
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                if i == 0 and "rapl" in group:
                    assert group not in report['groups']
                else:
                    assert group in report['groups']
        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_iter)
        assert pytest_wrapped.type == StopIteration


    def test_csvdb_second_rapl_missing(self):
        """
        Create two reports, one is full, second without rapl, then return None
        """
        csvdb = CsvDB(HWPCModel(), files_name=SECOND_RAPL_MISSING)
        csvdb.connect()
        group_name = [path.split('/')[-1] for path in SECOND_RAPL_MISSING]

        csvdb_iter = iter(csvdb)
        for i in range(2):
            report = next(csvdb_iter)
            for key in KEYS_COMMON:
                assert key in report
            for group in group_name:
                if i == 1 and "rapl" in group:
                    assert group not in report['groups']
                else:
                    assert group in report['groups']
        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_iter)
        assert pytest_wrapped.type == StopIteration

    ############
    #   Save   #
    ############

    def test_csvdb_save_header_error(self, corrupted_csvdb):
        """
        Try to save a PowerReport with an existent file and a corrupted header
        """
        csvdb = CsvDB(PowerModel(), current_path=PATH_TO_SAVE)
        csvdb.connect()

        # Try to save one PowerReport
        power_report = gen_power_report()
        with pytest.raises(HeaderAreNotTheSameError) as pytest_wrapped:
            csvdb.save(power_report.serialize())
        assert pytest_wrapped.type == HeaderAreNotTheSameError


    def test_csvdb_save_on(self, clean_csv_files):
        """
        Save a PowerReport from an basic object
        """
        csvdb = CsvDB(PowerModel(), current_path=PATH_TO_SAVE)
        csvdb.connect()

        power_reports = []

        # Save one time with a file that doesn't exist
        power_reports.append(gen_power_report())
        csvdb.save(power_reports[0].serialize())

        # Save three time
        for _ in range(3):
            power_reports.append(gen_power_report())
            csvdb.save(power_reports[-1].serialize())

        # Read the the csvdv and compare the data
        reading_power_reports = []
        csvdb_read = CsvDB(PowerModel(), [PATH_TO_SAVE + SENSOR + "-" + TARGET + "/PowerReport.csv"])
        csvdb_read.connect()
        csvdb_read_iter = iter(csvdb_read)

        for _ in range(4):
            reading_power_reports.append(csvdb_read.report_model.get_type().deserialize(next(csvdb_read_iter)))

        with pytest.raises(StopIteration) as pytest_wrapped:
            next(csvdb_read_iter)
        assert pytest_wrapped.type == StopIteration

        for i in range(4):
            if power_reports[i] != reading_power_reports[i]:
                assert False
