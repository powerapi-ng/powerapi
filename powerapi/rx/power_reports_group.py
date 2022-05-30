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
# Last modified : 18 mai 2022

##############################
#
# Imports
#
##############################
from datetime import datetime
from typing import Dict, Any

from powerapi.exception import BadInputDataException
from powerapi.quantity import PowerAPIQuantity
from powerapi.rx import Report
from powerapi.rx.report import TARGET_CN
from powerapi.rx.reports_group import ReportsGroup, TIMESTAMP_CN, SENSOR_CN, METADATA_CN, FIELDS_CN, TAGS_CN, \
    MEASUREMENT_CN

##############################
#
# Constants
#
##############################
POWER_CN = "power"

MEASUREMENT_NAME = "power_consumption"
UNIT_CN = "unit"

##############################
#
# Classes
#
##############################


class PowerReportsGroup(ReportsGroup):
    """ Class that enables the grouping of power reports by sensor, timestamp and metadata """

    def __init__(self, timestamp: datetime, sensor: str, report: Report, metadata: Dict = {}):
        """ Initialize an empty group
            Args:
                timestamp: The timestamp of the group
                sensor: The sensor related to the group
                report: The original report. It will be used to store reports with commons basic information
                metadata: The metadata related to the group

        """
        super().__init__(timestamp=timestamp, sensor=sensor, report=report, metadata=metadata)

    def to_mongodb_dict(self) -> [Dict]:
        """ Creates a list with the dict of each report row

            Return:
                A list with a dict representation of each report row

        """
        reports_dict = []
        # We get the dictionary with the basic information
        report_dict_basics = super()._to_mongodb_dict_basic_infos()

        # We create a dict for each line
        index_size = len(self.report.index)
        current_index = 0

        while current_index < index_size:
            current_report_dict = report_dict_basics
            current_row = self.report.iloc[current_index]
            current_report_dict[TARGET_CN] = current_row[TARGET_CN]
            current_report_dict[POWER_CN] = current_row[POWER_CN]
            reports_dict.append(current_report_dict)
            current_index += 1

        return reports_dict

    def to_influx_dict(self) -> [Dict]:
        """ Transforms the group report in a dict for influxdb

            Return:
                A list with a dict representation for influxdb of each report row

        """

        reports_dict = []
        # We get the dict with basic info
        report_dict_basics = super()._to_influx_basic_infos()

        # For each row we create a dictionary, we add the target, the power and the used units as a tag
        index_size = len(self.report.index)
        current_index = 0

        while current_index < index_size:
            current_report_dict = report_dict_basics
            current_row = self.report.iloc[current_index]
            current_report_dict[FIELDS_CN] = {POWER_CN: current_row[POWER_CN].magnitude}
            current_report_dict[TAGS_CN][UNIT_CN] = str(current_row[POWER_CN].units)
            current_report_dict[TAGS_CN][TARGET_CN] = str(current_row[TARGET_CN])
            current_report_dict[MEASUREMENT_CN] = MEASUREMENT_NAME

            reports_dict.append(current_report_dict)
            current_index += 1

        return reports_dict

    @staticmethod
    def create_reports_group_from_values(timestamp: datetime, sensor: str, target: str, power: PowerAPIQuantity,
                                  metadata: Dict[str, Any] = {}):
        """ Create a PowerReportsGroup with one row in a report by uing the provided information
            Args:
                timestamp: Dictionary that contains information of the report
                sensor: The name of the sensor
                target: The name of the target
                power: The power used for building the dataframe
                metadata: Dictionary containing the metadata
            Return:
                The list of names and values for building a multiindex as well as the report data
        """

        # We create the report
        report_data_dict = {TARGET_CN: [target], POWER_CN: [power]}
        report = Report(data=report_data_dict)

        # We create the Power Report
        return PowerReportsGroup(timestamp=timestamp, sensor=sensor,
                                 metadata=metadata, report=report)


    @staticmethod
    def create_reports_group_from_dicts(reports_dict: [Dict[str, Any]]):
        """ Creates a power group report by using the given information

            All the dictionaries have the same timestamp, sensor and metadata
            Args:
                reports_dict: List of dictionaries that contains information of the report
            Return :
                A new power group report created using information contained in the list of dictionaries
        """
        # We check that all the required information is in the input dictionary
        if not PowerReportsGroup.is_information_in_reports_dict(reports_dict):
            raise BadInputDataException(
                msg=f"One of the following infos is missing in at least one of the input dictionaries: {TIMESTAMP_CN}, "
                    f"{SENSOR_CN}, "
                    f"{TARGET_CN}, "
                    f"{POWER_CN}. The PowerReportsGroup cannot be created", input_data=reports_dict)

        # We create the report
        report_data_dict = {TARGET_CN: [], POWER_CN: []}

        for current_report_dict in reports_dict:
            report_data_dict[TARGET_CN].append(current_report_dict[TARGET_CN])
            report_data_dict[POWER_CN].append(current_report_dict[POWER_CN])

        report = Report(data=report_data_dict)

        # We get the basic infos from the first entry of the list
        current_report_dict = reports_dict[0]
        metadata = {} if METADATA_CN not in current_report_dict.keys() else current_report_dict[METADATA_CN]
        return PowerReportsGroup(timestamp=current_report_dict[TIMESTAMP_CN], sensor=current_report_dict[SENSOR_CN],
                                 metadata=metadata, report=report)

    @staticmethod
    def is_information_in_reports_dict(reports_dict: [Dict[str, Any]]) -> bool:
        """ Check if information is present in the given list of dictionaries

            Required information is basic information from report and power

            Args:
                reports_dict: List of dictionaries that contains information of the PowerReport

            Return:
                True if values are present, False otherwise
        """
        for current_report_dict in reports_dict:
            if not POWER_CN in current_report_dict.keys():
                return False
        return ReportsGroup.is_basic_information_in_reports_dict(reports_dict)

    def __repr__(self) -> str:
        return 'PowerGroupsReport(timestamp: {timestamp}, sensor: {sensor}, targets: {targets},' \
               'metadata: {metadata}), report:{report}'.format(timestamp=self.timestamp, sensor=self.sensor,
                                                               targets=sorted(self.get_targets()),
                                                               metadata=str(self.metadata), report=self.report)

