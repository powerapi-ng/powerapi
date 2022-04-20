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
# Last modified : 19 april 2022

##############################
#
# Imports
#
##############################
import time
from datetime import datetime
from typing import Dict, Any

from numpy import int64, float64
from pandas import DataFrame
from pandas import MultiIndex

from powerapi.exception import BadInputDataException

##############################
#
# Constants
#
##############################


METADATA_PREFIX = "metadata:"
METADATA_CN = "metadata"
TIMESTAMP_CN = "timestamp"
TARGET_CN = "target"
SENSOR_CN = "sensor"
INDEX_CN = "index"
INDEX_NAMES_CN = "index_names"
NUMBER_OF_BASIC_VALUES = 3
METADATA_PREFIX_LEN = len(METADATA_PREFIX)

MEASUREMENT_CN = "measurement"
TIME_CN = "time"
FIELDS_CN = "fields"
TAGS_CN = "tags"

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


##############################
#
# Classes
#
##############################
class Report(DataFrame):
    """ Class that represents a report in PowerAPI """

    def __init__(self, data: Dict, index_names: list, index_values: list, dtype=None):
        """ Initialize a report using the given parameters

        Args:
            data: The data related to the report
            index_names: Columns names used for building the multiindex
            index_values: List of tuples containing the values used for building the multiindex
        """

        super().__init__(data=data, index=MultiIndex.from_tuples(
            tuples=index_values,
            names=index_names), dtype=dtype)

    def to_dict(self) -> Dict:
        """ Transform the report in a dictionary

        Only index information is used for creating the dictionary.

        """

        # We get the basic information from the index
        timestamp_position = self.index.names.index(TIMESTAMP_CN)
        sensor_position = self.index.names.index(SENSOR_CN)
        target_position = self.index.names.index(TARGET_CN)
        report_dict = {TIMESTAMP_CN: self.index[0][timestamp_position], SENSOR_CN: self.index[0][sensor_position],
                       TARGET_CN: self.index[0][target_position]}

        # We get the metadata, we use METADATA_PREFIX to identify the metadata
        metadata = self.get_metadata()

        if len(metadata) > 0:
            report_dict[METADATA_CN] = metadata

        return report_dict

    def get_timestamp(self) -> str:
        """ Get the timestamp of the report

            Return
                The timestamp associated with the report

        """
        timestamp_position = self.index.names.index(TIMESTAMP_CN)
        return self.index[0][timestamp_position]

    def get_target(self) -> str:
        """ Get the target of the report

            Return
                The target associated with the report

        """
        target_position = self.index.names.index(TARGET_CN)
        return self.index[0][target_position]

    def get_sensor(self) -> str:
        """ Gets the sensor of the report

            Return
                The sensor associated with the report

        """
        sensor_position = self.index.names.index(SENSOR_CN)
        return self.index[0][sensor_position]

    def get_metadata(self) -> Dict:
        """ Gets a dictionary with report metadata

            Return
                Metadata dict that can be empty if there is no metadata
        """
        metadata = {}
        # We only look for metadata if it exists
        if len(self.index.names) > NUMBER_OF_BASIC_VALUES:
            value_position = 0
            for metadata_key in self.index.names:

                current_metadata_key = self._get_metadata_key_from_str(metadata_key)

                if current_metadata_key is not None:
                    current_value = self.index[0][value_position]

                    if isinstance(current_value, int64):
                        current_value = int(current_value)
                    elif isinstance(current_value, float64):
                        current_value = float(current_value)

                    metadata[current_metadata_key] = current_value

                value_position += 1
        return metadata

    def _get_metadata_key_from_str(self, metadata_key: str) -> str:

        """ Gets a metadata key

            Args:
                metadata_key: The metadata_key

            Return:
                 The metadata key or None if metadata_key does not contain METADTA_PRFEIX
        """
        prefix_position = metadata_key.find(METADATA_PREFIX)
        real_key = None

        if prefix_position != -1:
            real_key = metadata_key[prefix_position + METADATA_PREFIX_LEN:]

        return real_key

    def to_influx(self) -> Dict:
        """ Transforms the report in a dict for influxdb with basic info

            Basics info are metadata, sensor, target and time. The generated dict cannot not be used
            directly for storage in influxdb.

        """

        # We add the timestamp as a unix timestamp. The date has the format 2022-03-31T10:03:15.694Z
        influx_dict = {TIME_CN: int(time.mktime(datetime.strptime(self.get_timestamp(), DATE_FORMAT).timetuple()))}

        # We add the metadata, sensor and target
        metadata = self.get_metadata()
        metadata[SENSOR_CN] = self.get_sensor()
        metadata[TARGET_CN] = self.get_target()

        influx_dict[TAGS_CN] = metadata

        return influx_dict

    @staticmethod
    def create_report_from_dict(report_dict: Dict[str, Any]):
        """ Creates a report by using the given information

            Args:
                report_dict: Dictionary that contains information of the report
            Return :
                A new report created using information contained in the dictionary
        """
        # We check that all the required information is in the input dictionary
        if not Report.is_basic_information_in_report_dict(report_dict):
            raise BadInputDataException(
                msg=f"One of the following infos is missing in the input dictionary: {TIMESTAMP_CN}, "
                    f"{SENSOR_CN}, "
                    f"{TARGET_CN}. The report can not be created", input_data=report_dict)

        # We create the report
        metadata = {} if METADATA_CN not in report_dict.keys() else report_dict[METADATA_CN]
        return Report.create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                                target=report_dict[TARGET_CN], metadata=metadata)

    @staticmethod
    def create_report_from_values(timestamp: datetime, sensor: str, target: str, data: Dict[str, Any] = {},
                                  metadata: Dict[str, Any] = {}):
        """ Creates a report by using the given information

            Args:
                timestamp: Dictionary that contains information of the report
                sensor: The name of the sensor
                target: The name of the target
                data: The data not used for building the index
                metadata: Dictionary containing the metadata

            Return:
                A new report created using provided information. The report only contains information related to index
        """

        # We get index names and values

        index_names, index_values = Report.get_index_information_from_values(timestamp=timestamp, sensor=sensor,
                                                                             target=target, metadata=metadata)

        # We create the report
        return Report(data, index_names, index_values)

    @staticmethod
    def get_index_information_and_data_from_report_dict(report_dict: Dict) -> (list, list, Dict):
        """ Retrieves multiindex values and names and report data from a given dictionary containing the report information

            The basic values for building a multiindex are timestamp, sensor, target and metadata. The rest of information
            is considered as data as removed of a copy of report_dict

            Args:
                report_dict: The dictionary containing the information

            Return:
                The list of names and values for building a multiindex as well as the report data
        """

        # We get the index values
        timestamp = report_dict[TIMESTAMP_CN]
        sensor = report_dict[SENSOR_CN]
        target = report_dict[TARGET_CN]
        metadata = report_dict[METADATA_CN] if METADATA_CN in report_dict.keys() else {}

        # We define common index names and values
        index_names, index_values = Report.get_index_information_from_values(timestamp=timestamp, sensor=sensor,
                                                                             target=target,
                                                                             metadata=metadata)

        # We leave on the dictionary only the data not used for building the index
        data = report_dict.copy()

        del data[TIMESTAMP_CN]
        del data[SENSOR_CN]
        del data[TARGET_CN]

        if METADATA_CN in data.keys():
            del data[METADATA_CN]

        return index_names, index_values, data

    @staticmethod
    def get_index_information_from_values(timestamp: datetime, sensor: str, target: str,
                                          metadata: Dict[str, Any] = {}) -> (list, list):
        """ Gets multiindex values and names from given values

            The basic values for building a multiindex are timestamp, sensor, target and metadata.

            Args:
                timestamp: Dictionary that contains information of the report
                sensor: The name of the sensor
                target: The name of the target
                metadata: Dictionary containing the metadata

            Return:
                The list of names and values for building a multiindex
        """
        # We define common index names and values
        index_names = [TIMESTAMP_CN, SENSOR_CN, TARGET_CN]
        index_values = [(timestamp, sensor, target)]

        # Metadata is also part of the index
        for key, value in metadata.items():
            index_names.append(METADATA_PREFIX + key)
            for position, current_index in enumerate(index_values):
                index_values[position] = current_index + (value,)

        return index_names, index_values

    @staticmethod
    def is_basic_information_in_report_dict(report_dict: Dict[str, Any]) -> bool:
        """ Check is basic information is presen in the given dictionary

            Basic information are timestamp, sensor and target

            Args:
                report_dict: Dictionary that contains information of the report

            Return:
                True if values are present, False otherwise
        """
        keys = report_dict.keys()

        return (TIMESTAMP_CN in keys) and (SENSOR_CN in keys) and (TARGET_CN in keys)

    @staticmethod
    def is_information_in_report_dict(report_dict: Dict[str, Any]) -> bool:
        raise NotImplementedError
