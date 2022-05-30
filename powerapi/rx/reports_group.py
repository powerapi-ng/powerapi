# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

# Author : Daniel Romero Acero
# Last modified : 12 mai 2022

##############################
#
# Imports
#
##############################
from datetime import datetime
from typing import Dict, Any

from powerapi.exception import BadInputDataException
from powerapi.rx import Report

##############################
#
# Constants
#
##############################

# Mongodb
from powerapi.rx.report import TARGET_CN

METADATA_CN = "metadata"
TIMESTAMP_CN = "timestamp"
SENSOR_CN = "sensor"

# Influxdb
MEASUREMENT_CN = "measurement"
TIME_CN = "time"
FIELDS_CN = "fields"
TAGS_CN = "tags"
GENERIC_MEASUREMENT_NAME = 'generic_report'

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
DATE_FORMAT_WITHOUT_UTC_ADD = "%Y-%m-%dT%H:%M:%S.%f"


##############################
#
# Classes
#
##############################

class ReportsGroup:
    """ Class that enables the grouping of reports by sensor, timestamp and metadata """

    def __init__(self, timestamp: datetime, sensor: str, report: Report, metadata: Dict = {}):
        """ Initialize an empty group
            Args:
                timestamp: The timestamp of the group
                sensor: The sensor related to the group
                report: The original report. It will be used to store reports with commons basic information
                metadata: The metadata related to the group

        """
        self.timestamp = timestamp
        self.sensor = sensor
        self.metadata = metadata
        self.report = report  # A Dictionary of dictionaries. The key are

    def add_report(self, report: Report):
        """ Concat a report to the report's group

            Args:
                report: The report to add to the group
        """
        self.report.concat(report)

    def _to_mongodb_dict_basic_infos(self) -> Dict:
        """ Transform basic information of reports group in a mongodb dictionary

            Return:
                A dictionary that has sensor, timestamp and metadata as information

        """
        # We get the basic information from the index
        report_dict = {TIMESTAMP_CN: self.timestamp, SENSOR_CN: self.sensor}

        # We add metadata to the dictionary

        if len(self.metadata) > 0:
            report_dict[METADATA_CN] = self.metadata

        return report_dict

    def _to_influx_basic_infos(self) -> Dict:
        """ Transform basic information of reports group in a influxdb dictionary

            Return:
                A dictionary that has metadata, sensor and time as information. The generated dict cannot not be used
                directly for storage in influxdb.

        """

        # We add basic infos
        influx_dict = {TIME_CN: self.timestamp, TAGS_CN: self.metadata}  # Time in ms

        # We add sensor as a tag
        influx_dict[TAGS_CN][SENSOR_CN] = self.sensor

        return influx_dict

    @staticmethod
    def is_basic_information_in_reports_dict(reports_dict: [Dict[str, Any]]) -> bool:
        """ Check is basic information is present in the given dictionary

            Basic information are timestamp, sensor and target

            Args:
                reports_dict: List of dictionaries that contains information of the report

            Return:
                True if values are present, False otherwise
        """

        for current_report_dict in reports_dict:
            current_keys = current_report_dict.keys()
            if (not TIMESTAMP_CN in current_keys) or (not SENSOR_CN in current_keys) or (not TARGET_CN in current_keys):
                return False

        return True

    def to_mongodb_dict(self) -> [Dict]:
        """ Creates a list with the dict of each report row

            Return:
                A list with a dict representation of each report row

        """
        reports_dict = []
        # We get the dictionary with the basic information
        report_dict_basics = self._to_mongodb_dict_basic_infos()

        # We create a dict for each line
        index_size = len(self.report.index)
        current_index = 0

        while current_index < index_size:
            current_report_dict = report_dict_basics
            current_row = self.report.iloc[current_index]
            for current_column in self.report.columns:
                current_report_dict[current_column] = current_row[current_column]

            reports_dict.append(current_report_dict)
            current_index += 1

        return reports_dict

    def to_influx_dict(self) -> [Dict]:
        """ Transforms the group report in a dict for influxdb

            Return:
                A list with a dict representation for influxdb of each report row.
                There is not field data in the generated dicts

        """

        reports_dict = []
        # We get the dict with basic info
        report_dict_basics = self._to_influx_basic_infos()

        # For each row we create a dictionary, we add the target, the power and the used units as a tag
        index_size = len(self.report.index)
        current_index = 0

        while current_index < index_size:
            current_report_dict = report_dict_basics

            current_row = self.report.iloc[current_index]

            for current_column in self.report.columns:
                current_report_dict[TAGS_CN][current_column] = current_row[current_column]

            current_report_dict[MEASUREMENT_CN] = GENERIC_MEASUREMENT_NAME

            reports_dict.append(current_report_dict)
            current_index += 1

        return reports_dict

    @staticmethod
    def create_reports_group_from_dicts(reports_dict: [Dict[str, Any]]):
        """ Creates a group report by using the given information

            All the dictionaries have the same timestamp, sensor and metadata. The values on dictionaires have to be
            basic types. If they are a complex type, the creation can fail (cf. pandas Dataframe)

            Args:
                reports_dict: List of dictionaries that contains information of the report
            Return :
                A new power group report created using information contained in the list of dictionaries
        """
        # We check that all the required information is in the input dictionary
        if not ReportsGroup.is_basic_information_in_reports_dict(reports_dict):
            raise BadInputDataException(
                msg=f"One of the following infos is missing in at least one of the input dictionaries: {TIMESTAMP_CN}, "
                    f"{SENSOR_CN}, "
                    f"{TARGET_CN}. The ReportsGroup cannot be created", input_data=reports_dict)

        # We create the report
        report_data_dict = {}

        for current_report_dict in reports_dict:
            for current_column, current_value in current_report_dict.items():
                if current_column != TIMESTAMP_CN and current_column != SENSOR_CN and current_column != METADATA_CN:
                    if current_column not in report_data_dict.keys():
                        report_data_dict[current_column] = [current_value]
                    else:
                        report_data_dict[current_column].append(current_value)

        report = Report(data=report_data_dict)

        # We get the basic infos from the first entry of the list
        current_report_dict = reports_dict[0]
        metadata = {} if METADATA_CN not in current_report_dict.keys() else current_report_dict[METADATA_CN]
        return ReportsGroup(timestamp=current_report_dict[TIMESTAMP_CN], sensor=current_report_dict[SENSOR_CN],
                            metadata=metadata, report=report)

    @staticmethod
    def create_reports_group_from_values(timestamp: datetime, sensor: str, target: str,
                                         metadata: Dict[str, Any] = {}):
        """ Create a ReportsGroup with one row in a report by using the provided information
            Args:
                timestamp: Dictionary that contains information of the report group
                sensor: The name of the sensor
                target: The name of the target
                metadata: Dictionary containing the metadata
            Return:
                The report group
        """

        # We create the report
        report_data_dict = {TARGET_CN: [target]}
        report = Report(data=report_data_dict)

        # We create the Power Report
        return ReportsGroup(timestamp=timestamp, sensor=sensor, metadata=metadata, report=report)

    def __repr__(self) -> str:
        return 'GroupsReport(timestamp: {timestamp}, sensor: {sensor}, targets: {targets},' \
               'metadata: {metadata}), report:{report}'.format(timestamp=self.timestamp, sensor=self.sensor,
                                                               targets=sorted(self.get_targets()),
                                                               metadata=str(self.metadata), report=self.report)
