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
# Last modified : 17 March 2022

##############################
#
# Imports
#
##############################

from datetime import datetime
from typing import Dict, Any

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
        metadata = {}

        # We get the metadata, we use METADATA_PREFIX to identify the metadata
        metadata_prefix_len = len(METADATA_PREFIX)
        if len(self.index.names) > NUMBER_OF_BASIC_VALUES:
            value_position = NUMBER_OF_BASIC_VALUES
            for metadata_key in self.index.names[NUMBER_OF_BASIC_VALUES:]:

                current_metadata_key = self._get_metadata_key_from_str(metadata_key)

                if current_metadata_key is not None:
                    metadata[current_metadata_key] = self.index[0][value_position]

                value_position = value_position + 1

        if len(metadata) > 0:
            report_dict[METADATA_CN] = metadata

        return report_dict

    # def to_mongo_db(self):
    #     """ Transforms the report to a dict.
    #
    #         Only multiindex information will be included in the dictionary. If there are columns, specialized class
    #         has to deal with it
    #     """
    #     report_dict_tight = super().to_dict('tight')  # We use the dataframe method to be sure that there is not
    #     # numpy values
    #     # tight’ : dict like {‘index’ -> [index], ‘columns’ -> [columns], ‘data’ -> [values],
    #     # ‘index_names’ -> [index.names], ‘column_names’ -> [column.names]}
    #     print(report_dict_tight)
    #     report_dict = {}
    #     metadata = {}
    #     current_position = 0
    #
    #     for key in report_dict_tight[INDEX_NAMES_CN]:
    #         current_key = self._get_metadata_key_from_str(key)
    #
    #         if current_key is not None:
    #             metadata[current_key] = report_dict_tight[INDEX_CN][0][current_position]
    #         else:
    #             report_dict[key] = report_dict_tight[INDEX_CN][0][current_position]
    #
    #         current_position = current_position + 1
    #
    #     if len(metadata) > 0:
    #         report_dict[METADATA_CN] = metadata
    #
    #     return report_dict

    def _get_metadata_key_from_str(self, metadata_key: str) -> str:
        prefix_position = metadata_key.find(METADATA_PREFIX)
        real_key = None

        if prefix_position != -1:
            real_key = metadata_key[prefix_position + METADATA_PREFIX_LEN:]

        return real_key


##############################
#
# Functions for creating reports
#
##############################
def create_report_from_dict(report_dict: Dict[str, Any]) -> Report:
    """ Creates a report by using the given information

        Args:
            report_dict: Dictionary that contains information of the report
        Return :
            A new report created using information contained in the dictionary
    """
    # We check that all the required information is in the input dictionary
    if not is_basic_information_in_report_dict(report_dict):
        raise BadInputDataException(
            msg=f"One of the following infos is missing in the input dictionary: {TIMESTAMP_CN}, "
                f"{SENSOR_CN}, "
                f"{TARGET_CN}. The report can not be created", input_data=report_dict)

    # We create the report
    metadata = {} if METADATA_CN not in report_dict.keys() else report_dict[METADATA_CN]
    return create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                     target=report_dict[TARGET_CN], metadata=metadata)


def create_report_from_values(timestamp: datetime, sensor: str, target: str, data: Dict[str, Any] = {},
                              metadata: Dict[str, Any] = {}) -> Report:
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

    index_names, index_values = get_index_information_from_values(timestamp=timestamp, sensor=sensor,
                                                                  target=target, metadata=metadata)

    # We create the report
    return Report(data, index_names, index_values)


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
    index_names, index_values = get_index_information_from_values(timestamp=timestamp, sensor=sensor, target=target,
                                                                  metadata=metadata)

    # We leave on the dictionary only the data not used for building the index
    data = report_dict.copy()

    del data[TIMESTAMP_CN]
    del data[SENSOR_CN]
    del data[TARGET_CN]

    if METADATA_CN in data.keys():
        del data[METADATA_CN]

    return index_names, index_values, data


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
