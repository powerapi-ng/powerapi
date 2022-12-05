# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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
import shutil
import os
import csv

# from powerapi.report import create_core_report, create_group_report, create_report_root,\
#     create_socket_report
from powerapi.report import PowerReport, HWPCReport
from powerapi.database import CsvDB
from powerapi.database import CsvBadFilePathError, CsvBadCommonKeysError, HeaderAreNotTheSameError
from powerapi.utils import timestamp_to_datetime
from powerapi.test_utils.db.csv import ROOT_PATH

# All this file raise error
BAD_COMMON = [ROOT_PATH + "bad_common_miss_sensor.csv",
              ROOT_PATH + "bad_common_miss_target.csv",
              ROOT_PATH + "bad_common_miss_timestamp.csv"]

# Create 2 full HWPCReport
BASIC_FILES = [ROOT_PATH + "core2.csv",
               ROOT_PATH + "rapl2.csv",
               ROOT_PATH + "pcu2.csv"]

# Create 1 full HWPCReport (first miss)
FIRST_PRIMARY_MISSING = [ROOT_PATH + "core1_miss_first.csv",
                         ROOT_PATH + "rapl2.csv",
                         ROOT_PATH + "pcu2.csv"]

# Create 1 full HWPCReport (second miss)
SECOND_PRIMARY_MISSING = [ROOT_PATH + "core1_miss_second.csv",
                          ROOT_PATH + "rapl2.csv",
                          ROOT_PATH + "pcu2.csv"]

# Create 2 HWPCReport, first without rapl, second full
FIRST_RAPL_MISSING = [ROOT_PATH + "core2.csv",
                      ROOT_PATH + "rapl1_miss_first.csv",
                      ROOT_PATH + "pcu2.csv"]

# Create 2 HWPCReport, first full, second without rapl
SECOND_RAPL_MISSING = [ROOT_PATH + "core2.csv",
                       ROOT_PATH + "rapl1_miss_second.csv",
                       ROOT_PATH + "pcu2.csv"]

###################
# For CsvDB saving
###################

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


# def gen_hwpc_report():
#     """
#     Return a well formated HWPCReport
#     """
#     cpua0 = create_core_report('1', 'e0', '0')
#     cpub0 = create_core_report('2', 'e0', '1')
#     cpuc0 = create_core_report('3', 'e0', '2')
#     cpud0 = create_core_report('4', 'e0', '3')
#     cpua1 = create_core_report('1', 'e1', '0')
#     cpub1 = create_core_report('2', 'e1', '1')
#     cpuc1 = create_core_report('3', 'e1', '2')
#     cpud1 = create_core_report('4', 'e1', '3')

#     socketa0 = create_socket_report('1', [cpua0, cpub0])
#     socketb0 = create_socket_report('2', [cpuc0, cpud0])
#     socketa1 = create_socket_report('1', [cpua1, cpub1])
#     socketb1 = create_socket_report('2', [cpuc1, cpud1])

#     groupa = create_group_report('group1', [socketa0, socketb0])
#     groupb = create_group_report('group2', [socketa1, socketb1])

#     return create_report_root([groupa, groupb])


def gen_power_report():
    global CPT
    CPT += 1
    return PowerReport(timestamp_to_datetime(CPT), SENSOR, TARGET, 0.11,
                       {'mdt_socket': '-1', 'metadata1': 'truc', 'metadata2': 'oui'})


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


@pytest.fixture()
def power_csvdb():
    return CsvDB(PowerReport, ['socket'], current_path=os.getcwd())


@pytest.fixture()
def hwpc_csvdb():
    return CsvDB(HWPCReport, ['socket'], current_path=os.getcwd())


##################
#     TESTS      #
##################

class TestCsvDB():
    """
    Test class of CsvDB class
    """

    def test_csvdb_bad_filepath(self, power_csvdb):
        """
        Test with bad filepath
        """
        with pytest.raises(CsvBadFilePathError) as pytest_wrapped:
            power_csvdb.add_file("/tmp/unknowfile.csv")
            power_csvdb.connect()
            power_csvdb.iter(False)
        assert pytest_wrapped.type == CsvBadFilePathError

    def test_csvdb_bad_common(self, power_csvdb):
        """
        Test when file miss some common column
        """
        csv_files = BAD_COMMON
        while csv_files:
            with pytest.raises(CsvBadCommonKeysError) as pytest_wrapped:
                power_csvdb.add_files(csv_files)
                power_csvdb.connect()
                power_csvdb.iter(False)
            assert pytest_wrapped.type == CsvBadCommonKeysError
            csv_files = csv_files[1:]

    def test_csvdb_two_reports(self, hwpc_csvdb):
        """
        Create two full HWPCReport, then return None
        """
        hwpc_csvdb.add_files(BASIC_FILES)
        hwpc_csvdb.connect()
        group_name = [path.split('/')[-1][:-4] for path in BASIC_FILES]

        csvdb_iter = hwpc_csvdb.iter(False)
        for _ in range(2):
            report = next(csvdb_iter)
            for group in group_name:
                assert group in report.groups

        with pytest.raises(StopIteration) as _:
            next(csvdb_iter)

    def test_csvdb_first_primary_missing(self, hwpc_csvdb):
        """
        Create one full HWPCReport (the second), then return None
        """
        hwpc_csvdb.add_files(FIRST_PRIMARY_MISSING)
        hwpc_csvdb.connect()
        group_name = [path.split('/')[-1][:-4] for path in FIRST_PRIMARY_MISSING]

        csvdb_iter = hwpc_csvdb.iter(False)
        report = next(csvdb_iter)
        for group in group_name:
            assert group in report.groups
        assert report.timestamp == timestamp_to_datetime(1539260665189)
        with pytest.raises(StopIteration) as _:
            next(csvdb_iter)

    def test_csvdb_second_primary_missing(self, hwpc_csvdb):
        """
        Create one full HWPCReport (the first), then return None
        """
        hwpc_csvdb.add_files(SECOND_PRIMARY_MISSING)
        hwpc_csvdb.connect()
        group_name = [path.split('/')[-1][:-4] for path in SECOND_PRIMARY_MISSING]

        csvdb_iter = hwpc_csvdb.iter(False)
        report = next(csvdb_iter)
        for group in group_name:
            assert group in report.groups
        assert report.timestamp == timestamp_to_datetime(1539260664189)
        with pytest.raises(StopIteration) as _:
            next(csvdb_iter)

    def test_csvdb_first_rapl_missing(self, hwpc_csvdb):
        """
        Create two reports, one without rapl, second is full, then return None
        """
        hwpc_csvdb.add_files(FIRST_RAPL_MISSING)
        hwpc_csvdb.connect()
        group_name = [path.split('/')[-1][:-4] for path in FIRST_RAPL_MISSING]

        csvdb_iter = hwpc_csvdb.iter(False)
        for i in range(2):
            report = next(csvdb_iter)
            for group in group_name:
                if i == 0 and "rapl" in group:
                    assert group not in report.groups
                else:
                    assert group in report.groups
        with pytest.raises(StopIteration) as _:
            next(csvdb_iter)

    def test_csvdb_second_rapl_missing(self, hwpc_csvdb):
        """
        Create two reports, one is full, second without rapl, then return None
        """
        hwpc_csvdb.add_files(SECOND_RAPL_MISSING)
        hwpc_csvdb.connect()
        group_name = [path.split('/')[-1][:-4] for path in SECOND_RAPL_MISSING]

        csvdb_iter = hwpc_csvdb.iter(False)
        for i in range(2):
            report = next(csvdb_iter)
            for group in group_name:
                if i == 1 and "rapl" in group:
                    assert group not in report.groups
                else:
                    assert group in report.groups
        with pytest.raises(StopIteration) as _:
            next(csvdb_iter)

    ############
    #   Save   #
    ############

    def test_csvdb_save_header_error(self, corrupted_csvdb):
        """
        Try to save a PowerReport with an existent file and a corrupted header
        """
        csvdb = CsvDB(PowerReport, ['mdt_socket'], current_path=PATH_TO_SAVE)
        csvdb.connect()

        # Try to save one PowerReport
        power_report = gen_power_report()
        with pytest.raises(HeaderAreNotTheSameError) as _:
            csvdb.save(power_report)

    def test_csvdb_save_on(self, clean_csv_files):
        """
        Save a PowerReport from an basic object
        """
        csvdb = CsvDB(PowerReport, ['mdt_socket'], current_path=PATH_TO_SAVE)
        csvdb.connect()

        power_reports = list()

        # Save one time with a file that doesn't exist
        power_reports.append(gen_power_report())
        csvdb.save(power_reports[0])

        # Save three time
        for _ in range(3):
            power_reports.append(gen_power_report())
            csvdb.save(power_reports[-1])

        # Read the the csvdb and compare the data
        reading_power_reports = []
        csvdb_read = CsvDB(PowerReport, ['mdt_socket'], current_path=PATH_TO_SAVE)
        csvdb_read.add_file(PATH_TO_SAVE + SENSOR + "-" + TARGET + "/PowerReport.csv")
        csvdb_read.connect()
        csvdb_read_iter = csvdb_read.iter(False)

        for _ in range(4):
            reading_power_reports.append(next(csvdb_read_iter))

        with pytest.raises(StopIteration) as _:
            next(csvdb_read_iter)

        for i in range(4):
            assert power_reports[i] == reading_power_reports[i]
