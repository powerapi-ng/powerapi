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
from powerapi.report import PowerReport
from powerapi.report_model import ReportModel, BadInputData
from powerapi.report_model import CSV_HEADER_POWER
from powerapi.utils import timestamp_to_datetime, datetime_to_timestamp


class PowerModel(ReportModel):
    """
    PowerModel class.

    It define all the function that need to be override if we want
    to format the raw data read in different kind of database.

    {
        'PowerReport' : {
            'timestamp': ...
            'sensor': ...
            'target': ...
            'power': ...
            'metadata': {
                ...
            }
        }
    }

    """

    def get_type(self):
        """
        Return the type of report
        """
        return PowerReport

    def to_influxdb(self, serialized_report) -> Dict:
        """
        Return raw data from serialized report

        {
            'measurement' : 'power_consumption'
                'timestamp': ...
                'tags' : { ... }
                'fields': {
                    'power': ...
                }
        }
        """

        if ('sensor' not in serialized_report or 'target' not in serialized_report
            or 'metadata' not in serialized_report or 'timestamp' not in serialized_report
            or 'power' not in serialized_report):
            raise BadInputData()

        tags = {'sensor': serialized_report['sensor'],
                'target': serialized_report['target']}

        for name in serialized_report['metadata'].keys():
            if name == 'ratio':
                pass
            else:
                tags[name] = serialized_report['metadata'][name]
            

        return {
            'measurement': 'power_consumption',
            'tags': tags,
            'time': str(serialized_report['timestamp']),
            'fields': {
                'power': serialized_report['power']
            }
        }

    def to_csvdb(self, serialized_report) -> Tuple[List[str], Dict]:
        """
        Return raw data from serialized report

        {
            'PowerReport' : [{
                'timestamp': ...
                'sensor': ...
                'target': ...
                'power': ...
                'metadata': {
                    ...
                }
            }]
        }
        """
        final_dict = {}
        try:
            for field in CSV_HEADER_POWER:
                final_dict[field] = serialized_report[field]

            final_dict['timestamp'] = datetime_to_timestamp(serialized_report['timestamp'])

            for key, val in serialized_report['metadata'].items():
                final_dict[key] = val

        except KeyError:
            raise BadInputData()

        final_dict = {self.get_type().__name__: [final_dict]}
        return CSV_HEADER_POWER, final_dict

    def from_csvdb(self, file_name, row) -> Dict:
        """
        Get the csvdb report

        {
            'timestamp': ...
            'sensor': ...
            'target': ...
            'power': ...
            'metadata': {
                ...
            }
        }
        """
        final_dict: Dict = {}

        try:
            final_dict = {key: row[key] for key in CSV_HEADER_POWER}
            final_dict['timestamp'] = timestamp_to_datetime(int(row['timestamp']))
            final_dict['power'] = float(row['power'])
            final_dict['metadata'] = {}
            for key in row.keys():
                if key not in CSV_HEADER_POWER:
                    final_dict['metadata'][key] = row[key]
        except KeyError:
            raise BadInputData()

        return final_dict

    def to_mongodb(self, serialized_report) -> Dict:
        """
        Return raw data from serialized report

        {
            'timestamp': ...
            'sensor': ...
            'target': ...
            'power': ...
            'metadata': {
                ...
            }
        }
        """
        return serialized_report

    def from_mongodb(self, json) -> Dict:
        """
        Get the mongodb report

        {
            'timestamp': ...
            'sensor': ...
            'target': ...
            'power': ...
            'metadata': {
                ...
            }
        }
        """
        # Re arrange the json before return it by removing '_id' field
        json.pop('_id', None)

        return json
