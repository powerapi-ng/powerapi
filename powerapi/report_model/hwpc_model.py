"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from powerapi.report_model import ReportModel, KEYS_CSV_COMMON, KEYS_COMMON, BadInputData
from powerapi.report import HWPCReport


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

    def from_mongodb(self, json):
        """
        Get HWPCReport from a MongoDB database.
        """
        # Re arrange the json before return it by removing '_id' field
        json.pop('_id', None)

        return json

    def from_csvdb(self, file_name, row):
        """
        Get HWPCReport from a few csv files.
        """
        final_dict = {}

        try:
            final_dict = {key: row[key] for key in KEYS_COMMON}
            final_dict['groups'] = {}

            # If group doesn't exist, create it
            if file_name not in final_dict:
                final_dict['groups'][file_name] = {}

            # If socket doesn't exist, create it
            if row['socket'] not in final_dict['groups'][file_name]:
                final_dict['groups'][file_name][row['socket']] = {}

            # If cpu doesn't exist, create it
            if row['cpu'] not in final_dict['groups'][file_name][row['socket']]:
                final_dict['groups'][file_name][row['socket']][row['cpu']] = {}

            # Add events
            for key, value in row.items():
                if key not in KEYS_CSV_COMMON:
                    final_dict['groups'][file_name][
                        row['socket']][row['cpu']][key] = int(value)

        except KeyError:
            raise BadInputData()

        return final_dict
