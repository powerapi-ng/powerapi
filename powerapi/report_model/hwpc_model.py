# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from typing import Dict, List, Tuple
from powerapi.report_model import ReportModel, CSV_HEADER_COMMON, CSV_HEADER_HWPC, BadInputData
from powerapi.report import HWPCReport
from powerapi.utils import datetime_to_timestamp, timestamp_to_datetime


class HWPCModel(ReportModel):
    """
    HWPCModel class.

    It define all the function for get the hwpc necessary field from
    any kind of database.
    """

    def get_type(self):
        """
        Return the type of report
        """
        return HWPCReport

    def from_mongodb(self, json) -> Dict:
        """
        Get HWPCReport from a MongoDB database.

        {
         'timestamp': $int,
         'sensor': '$str',
         'target': '$str',
         'groups' : {
            '$group_name': {
               '$socket_id': {
                   '$core_id': {
                       '$event_name': '$int',
                       ...
                   }
                   ...
               }
               ...
            }
            ...
        }
        """
        # Re arrange the json before return it by removing '_id' field
        json.pop('_id', None)

        return json

    def to_mongodb(self, serialized_report) -> Dict:
        """
        :param serialized_report: Serialized report
        """
        return serialized_report

    def from_csvdb(self, file_name, row) -> Dict:
        """
        Get HWPCReport from a few csv files.
        """
        final_dict = {}

        try:
            group_name = file_name[:-4] if file_name[len(file_name)-4:] == '.csv' else file_name
            final_dict = {key: row[key] for key in CSV_HEADER_COMMON}
            final_dict['timestamp'] = timestamp_to_datetime(int(row['timestamp']))
            final_dict['groups'] = {}

            # If group doesn't exist, create it
            if group_name not in final_dict:
                final_dict['groups'][group_name] = {}

            # If socket doesn't exist, create it
            if row['socket'] not in final_dict['groups'][group_name]:
                final_dict['groups'][group_name][row['socket']] = {}

            # If cpu doesn't exist, create it
            if row['cpu'] not in final_dict['groups'][group_name][row['socket']]:
                final_dict['groups'][group_name][row['socket']][row['cpu']] = {}

            # Add events
            for key, value in row.items():
                if key not in CSV_HEADER_HWPC:
                    final_dict['groups'][group_name][
                        row['socket']][row['cpu']][key] = int(value)

        except KeyError:
            raise BadInputData()

        return final_dict

    def to_csvdb(self, serialized_report) -> Tuple[List[str], Dict]:
        """
        Return raw data from serialized report
        :return: Header, Dict(str, List(Dict))
        """
        basic_csv_row = {key: serialized_report[key] for key in CSV_HEADER_COMMON}
        # timestamp
        basic_csv_row['timestamp'] = datetime_to_timestamp(basic_csv_row['timestamp'])

        final_dict = {}

        try:
            for group_name, sockets in serialized_report['groups'].items():
                new_csv_row = basic_csv_row.copy()
                for socket_name, cpus in sockets.items():
                    new_csv_row['socket'] = socket_name
                    for cpu_name, events in cpus.items():
                        new_csv_row['cpu'] = cpu_name
                        for event_name, value in events.items():
                            new_csv_row[event_name] = value

                        # add in final dict
                        if group_name in final_dict:
                            final_dict[group_name].append(new_csv_row.copy())
                        else:
                            final_dict[group_name] = [new_csv_row.copy()]
        except KeyError:
            raise BadInputData()

        return CSV_HEADER_HWPC, final_dict
