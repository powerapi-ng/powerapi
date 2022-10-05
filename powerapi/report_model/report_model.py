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
from powerapi.exception import PowerAPIException


CSV_HEADER_COMMON = ['timestamp', 'sensor', 'target']
CSV_HEADER_HWPC = CSV_HEADER_COMMON + ['socket', 'cpu']
CSV_HEADER_POWER = CSV_HEADER_COMMON + ['power']


class BadInputData(PowerAPIException):
    """
    Exception raised when the data read in input are not
    in the good format
    """


class ReportModel:
    """
    ReportModel class.

    It define all the function that need to be override if we want
    to format the raw data read in different kind of database.
    """

    def get_type(self):
        """
        Return the type of report
        """
        raise NotImplementedError()

    def from_mongodb(self, json) -> Dict:
        """
        Get the mongodb report
        """
        raise NotImplementedError()

    def from_csvdb(self, file_name, row) -> Dict:
        """
        Get the csvdb report
        """
        raise NotImplementedError()

    def to_mongodb(self, serialized_report) -> Dict:
        """
        Return raw data from serialized report
        """
        raise NotImplementedError()

    def to_csvdb(self, serialized_report) -> Tuple[List[str], Dict]:
        """
        Return raw data from serialized report
        """
        raise NotImplementedError()
