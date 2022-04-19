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

# Author: Daniel Romero Acero
# Last modified: 18 March 2022

##############################
#
# Imports
#
##############################
import pint  # Event if these modules are not explicitly used, they are required for using pint with pandas
import pint_pandas

from datetime import datetime
from typing import Dict, Any

from numpy import int64, float64, nan
from pandas import isna

from powerapi.exception import BadInputDataException
from powerapi.quantity import PowerAPIPint_MODULE_NAME
from powerapi.rx.report import get_index_information_and_data_from_report_dict, get_index_information_from_values, \
    Report, is_basic_information_in_report_dict, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN

##############################
#
# Constants
#
##############################
GROUPS_CN = "groups"
SOCKET_CN = "socket_id"
CORE_CN = "core_id"


##############################
#
# Classes
#
##############################

class HWPCReport(Report):
    """ HWPC Report """

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """ Creates a HWPC Report

        Args:
            data: The data related to the HWPC report
            index_names: Columns names used for building the multiindex
            index_values: List of tuples containing the values used for building the multiindex
        """
        super().__init__(data=data, index_names=index_names, index_values=index_values)

    def to_dict(self) -> Dict:
        """ Transform a HWPC report in a dictionary

        Index information and groups are used for creating the dictionary.

        """
        # We get the dictionary with the basic information
        report_dict = super().to_dict()

        # We have to create a dictionary for each group
        groups = {}
        groups_position = self.index.names.index(GROUPS_CN)
        socket_position = self.index.names.index(SOCKET_CN)
        core_position = self.index.names.index(CORE_CN)

        for current_index in self.index:
            current_group_key = current_index[groups_position]
            current_socket_key = current_index[socket_position]
            current_core_key = current_index[core_position]

            # We create the group if required
            if current_group_key not in groups.keys():
                groups[current_group_key] = {}

            current_group_dict = groups[current_group_key]

            # We create the group l1 if required
            if current_socket_key not in current_group_dict.keys():
                current_group_dict[current_socket_key] = {}

            current_socket_dict = current_group_dict[current_socket_key]

            # We create the group l2 if required

            if current_core_key not in current_socket_dict.keys():
                current_socket_dict[current_core_key] = {}

            current_core_dict = current_socket_dict[current_core_key]

            # We get the data related to the current core
            current_core_data = self.loc[current_index]

            for current_column in current_core_data.index:
                current_core_value = current_core_data.at[current_column]
                if isinstance(current_core_value, int64) and current_core_value is not nan:
                    current_core_value = int(current_core_value)
                elif isinstance(current_core_value, float64) and current_core_value is not nan:
                    current_core_value = float(current_core_value)

                # We only add the entry if it exists, i.e., it is not nan
                if not isna(current_core_value):
                    current_core_dict[current_column] = current_core_value

        # We add the data, i.e., information that is not in the index
        report_dict[GROUPS_CN] = groups
        return report_dict


##############################
#
# Functions
#
##############################

def create_report_from_dict(report_dict: Dict[str, Any]) -> HWPCReport:
    """ Creates a HWPC report by using the given information

        Args:
            report_dic: Dictionary that contains information of the HWPC report
    """

    # We check that all the required information is in the input dictionary
    if not is_information_in_hwpc_report_dict(report_dict):
        raise BadInputDataException(msg=f"The {GROUPS_CN} info is missing in the input dictionary. "
                                        f"The HWPC Report can not be created", input_data=report_dict)

    # We check that groups is a dictionary
    if not isinstance(report_dict[GROUPS_CN], Dict):
        raise BadInputDataException(msg=f"The groups has to be a dictionary. The HWPC Report can not be created "
                                    , input_data=report_dict[GROUPS_CN])

    metadata = {} if METADATA_CN not in report_dict.keys() else report_dict[METADATA_CN]

    return create_hwpc_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                          target=report_dict[TARGET_CN], groups_dict=report_dict[GROUPS_CN],
                                          metadata=metadata)


def create_hwpc_report_from_values(timestamp: datetime, sensor: str, target: str, groups_dict: Dict,
                                   metadata: Dict[str, Any] = {}) -> HWPCReport:
    """ Creates a hwpc report by using the given information

        Args:
            timestamp: Dictionary that contains information of the report
            sensor: The name of the sensor
            target: The name of the target
            groups_dict: The data not used for building the HWPC dataframe
            metadata: Dictionary containing the metadata

        Return:
            A new report created using provided information. The report only contains information related to index
    """

    # We get index names and values
    index_names, index_values = get_index_information_from_values(timestamp=timestamp, sensor=sensor, target=target,
                                                                  metadata=metadata)

    # We add the groups and socket keys and core keys as part of the index
    index_names.append(GROUPS_CN)
    index_names.append(SOCKET_CN)
    index_names.append(CORE_CN)

    # For each existing index_value, we have to add values related to groups' keys
    columns_data = {}
    number_of_values_added = 0
    original_index_value = index_values[0]  # There is only one entry

    row_size = 0

    for group_key in groups_dict.keys():

        # We add the group level values to the index

        # We add the socket values to the index
        current_socket_dict = groups_dict[group_key]

        for socket_key in current_socket_dict.keys():

            # We add the core values to the index
            current_core_dict = current_socket_dict[socket_key]

            for core_key in current_core_dict.keys():
                value_to_add = original_index_value + (group_key, socket_key, core_key,)
                if number_of_values_added < len(index_values):
                    index_values[number_of_values_added] = value_to_add
                else:
                    index_values.append(value_to_add)

                number_of_values_added = number_of_values_added + 1

                # We extract the data from the core
                data_values = current_core_dict[core_key]
                for data_key in data_values:
                    current_value_to_add = data_values[data_key]
                    if data_key not in columns_data.keys():
                        columns_data[data_key] = []
                        current_row_size = 0

                        # We have to fill up empty values in the row with None
                        while current_row_size < row_size:
                            columns_data[data_key].append(None)
                            current_row_size += 1

                    columns_data[data_key].append(current_value_to_add)
                row_size += 1

    # All the columns must have the same size
    for column_name in columns_data.keys():
        while len(columns_data[column_name]) < row_size:
            columns_data[column_name].append(None)

    # We create the HWPC Report
    return HWPCReport(columns_data, index_names, index_values)


def is_information_in_hwpc_report_dict(report_dict: Dict[str, Any]) -> bool:
    """ Check if information is present in the given dictionary

        Required information is basic information from report and groups

        Args:
            report_dict: Dictionary that contains information of the HWPC report

        Return:
            True if values are present, False otherwise
    """
    return (GROUPS_CN in report_dict.keys()) and is_basic_information_in_report_dict(report_dict)
