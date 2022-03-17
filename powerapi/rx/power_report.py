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

# Author : Daniel  Romero Acero
# Last modified : 17 march 2022

##############################
#
# Imports
#
##############################
from datetime import datetime
from typing import Dict, Any

from powerapi.exception import BadInputDataException
from powerapi.rx.report import get_index_information_and_data_from_report_dict, get_index_information_from_values, \
    Report, is_basic_information_in_report_dict

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
    """Fake Report for testing purposes"""

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """ Creates a fake formula

        Args:

        """
        super().__init__(data=data, index_names=index_names, index_values=index_values)

    def to_dict(self) -> Dict:

        """ Transform a power report in a dictionary

        Only index information is used for creating the dictionary.

        """
        # We get the dictionary with the basic information
        report_dict = super().to_dict()

        # We have to add the power information

        power_position = self.index.names.index(POWER_CN)

        report_dict[POWER_CN] = self.index[0][power_position]

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
    if not is_basic_information_in_power_report_dict(report_dict):
        raise BadInputDataException(msg=f"One of the following info is missing in the input dictionary: {POWER_CN}. "
                                        f"The power report can not be created", input_data=report_dict)

    # We get index names and values. The rest of information are considered as data for the dataframe

    index_names, index_values, data = get_index_information_and_data_from_report_dict(report_dict)

    # We include also the power column in the index and remove it from data
    index_names.append(POWER_CN)
    index_values[0] = index_values[0] + (data[POWER_CN],)  # A power report only has an index

    del data[POWER_CN]

    # We create the report
    return PowerReport(data=data, index_names=index_names, index_values=index_values)


def create_power_report_from_values(timestamp: datetime, sensor: str, target: str, power: float,
                                    data: Dict[str, Any] = {}, metadata: Dict[str, Any] = {}) -> Report:
    """ Creates a power report by using the given information

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

    # We include also the power column in the index and remove it from data
    index_names.append(POWER_CN)
    index_values = index_values + (power,)

    # We create the report
    return Report(data, index_names, index_values)


def is_basic_information_in_power_report_dict(report_dict: Dict[str, Any]) -> bool:
    """ Check is basic information is presen in the given dictionary

        Basic information are {TIMESTAMP_CN}, {SENSOR_CN} and {TARGET_CN}

        Args:
            report_dict: Dictionary that contains information of the report

        Return:
            True if values are present, False otherwise
    """
    return (POWER_CN in report_dict.keys()) and is_basic_information_in_report_dict(report_dict)
