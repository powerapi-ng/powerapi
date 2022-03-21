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
# Last modified: 17 March 2022

##############################
#
# Imports
#
##############################
import pint  # Event if these modules are not explicitly used, they are required for using pint with pandas
import pint_pandas

from datetime import datetime
from typing import Dict, Any

from powerapi.exception import BadInputDataException
from powerapi.quantity import PowerAPIPint_MODULE_NAME, PowerAPIQuantity
from powerapi.rx.report import get_index_information_and_data_from_report_dict, get_index_information_from_values, \
    Report, is_basic_information_in_report_dict, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN

##############################
#
# Constants
#
##############################
POWER_CN = "power"


##############################
#
# Classes
#
##############################

class PowerReport(Report):
    """ Power Report """

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """ Creates a Power Report

        Args:
            data: It contains power value
            index_names: Columns names used for building the multiindex
            index_values: List of tuples containing the values used for building the multiindex
        """
        super().__init__(data=data, index_names=index_names, index_values=index_values,
                         dtype=PowerAPIPint_MODULE_NAME + "[" + data[POWER_CN][0].units.__str__() + "]")

    def to_dict(self) -> Dict:
        """ Transform a power report in a dictionary

        Index information and power value are used for creating the dictionary.

        """
        # We get the dictionary with the basic information
        report_dict = super().to_dict()

        # We have to add the power information
        report_dict[POWER_CN] = self.loc[self.index[0]].at[POWER_CN]

        return report_dict


##############################
#
# Functions
#
##############################

def create_power_report_from_dict(report_dict: Dict[str, Any]) -> PowerReport:
    """ Creates a power report by using the given information

        Args:
            report_dict: Dictionary that contains information of the power report
        Return :
            A new power report created using information contained in the dictionary
    """

    # We check that all the required information is in the input dictionary
    if not is_information_in_power_report_dict(report_dict):
        raise BadInputDataException(msg=f"The {POWER_CN} info is missing in the input dictionary. "
                                        f"The Power Report can not be created", input_data=report_dict)

    # We check that the power is a quantity
    if not isinstance(report_dict[POWER_CN], PowerAPIQuantity):
        raise BadInputDataException(msg=f"The power has to be a PowerAPIQuantity. The Power Report can not be created "
                                    , input_data=report_dict[POWER_CN])

    metadata = {} if METADATA_CN not in report_dict.keys() else report_dict[METADATA_CN]

    # We create the Power Report
    return create_power_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                           target=report_dict[TARGET_CN], power=report_dict[POWER_CN],
                                           metadata=metadata)


def create_power_report_from_values(timestamp: datetime, sensor: str, target: str, power: PowerAPIQuantity,
                                    metadata: Dict[str, Any] = {}) -> PowerReport:
    """ Retrieves multiindex values and names and report data from a given dictionary containing the report information

        The basic values for building a multiindex are timestamp, sensor, target and metadata. The rest of information
        is considered as data as removed of a copy of report_dict

        Args:
            timestamp: Dictionary that contains information of the report
            sensor: The name of the sensor
            target: The name of the target
            power: The power used for building the dataframe
            metadata: Dictionary containing the metadata

        Return:
            The list of names and values for building a multiindex as well as the report data
    """

    # We get index names and values
    index_names, index_values = get_index_information_from_values(timestamp=timestamp, sensor=sensor,
                                                                  target=target, metadata=metadata)

    # We include the power as data in the dataframe
    power_data = {POWER_CN: [power]}

    # We create the Power Report
    return PowerReport(data=power_data, index_names=index_names, index_values=index_values)


def is_information_in_power_report_dict(report_dict: Dict[str, Any]) -> bool:
    """ Check is basic information is present in the given dictionary

        Required information is basic information from report and the  power value

        Args:
            report_dict: Dictionary that contains information of the report

        Return:
            True if values are present, False otherwise
    """
    return (POWER_CN in report_dict.keys()) and is_basic_information_in_report_dict(report_dict)
