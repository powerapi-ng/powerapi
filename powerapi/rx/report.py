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

from typing import Dict, Any

from pandas import DataFrame



##############################
#
# Constants
#
##############################

TARGET_CN = "target"


##############################
#
# Classes
#
##############################
class Report(DataFrame):
    """ Class that represents a report in PowerAPI """

    def __init__(self, data: Dict, index: Any = None, dtype=None):
        """ Initialize a report using the given parameters

        Args:
            data: The data specific to the report. Each key is a column name and values are list with the associated
                  columns values
            index: The index of the dataframe
            dtype: The type of the dataframe values
        """

        super().__init__(data=data, index=index, dtype=dtype)

    def get_targets(self) -> [str]:
        """ Returns a list with the targets of the report

            Return:
                List of targets
        """
        return self.groupby(TARGET_CN).indices.keys()

    def __repr__(self) -> str:
        return 'Report(targets: {targets}, row count:{rows}, columns:{columns}'. \
            format(targets=self.get_targets(), rows=len(self), columns=list(self.columns))
