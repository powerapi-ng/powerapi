# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import numpy as np

class StatBuffer:
    """
    Buffer that store timeseries values and compute statistics on it
    """

    def __init__(self, aggregation_periode: int):
        """
        :param aggregation_periode: number of second for the value must be aggregated before compute statistics on them
        """

        self.aggregation_periode = aggregation_periode
        self.buffer = {}

    def append(self, measure: Dict, key: str):
        """
        append a measure to the buffer

        measure must have the following format :

        {
          'tags': Dict,
          'time': int,
          'value': float,
        }
        """
        if key not in self.buffer:
            self.buffer[key] = []

        self.buffer[key].append(measure)

    def is_available(self, key: str) -> bool:
        """
        Return true if they are enough value for the given key to compute a statistics (depend on aggregation periode parameter)
        :raise KeyError: if no measure were append with this key before
        """
        if key not in self.buffer:
            raise KeyError

        first_measure = self.buffer[key][0]
        last_measure = self.buffer[key][-1]

        return (last_measure['time'] - first_measure['time']) >= self.aggregation_periode

    def _compute_stats(self, values: List[float]) -> Tuple[float, float]:
        """
        :return: mean, std
        """
        np_values = np.array([value['value'] for value in values])
        return np_values.mean(), np_values.std()

    def _split_values(self, values: List[Dict]):
        time_of_first_measure = values[0]['time']
        
        def split(value_in_periode, value_out_periode):
            if value_out_periode == []:
                return value_in_periode, value_out_periode
            if value_out_periode[0]['time'] - time_of_first_measure > self.aggregation_periode:
                return value_in_periode, value_out_periode
            else:
                val = value_out_periode.pop(0)
                value_in_periode.append(val)
                return split(value_in_periode, value_out_periode)

        return split([], values)
        
    
    def get_stats(self, key: str) -> Dict:
        """
        return statistics on the values corresponding to the given key

        :return: a dictionary with this format:
        :raise KeyError: if no measure were append with this key before
        {
          'mean': float,
          'std': float,
          'time': int, # timestamp of the last measure
          'tags': Dict,
        }
        return None if no statistics are available
        """
        if not self.is_available(key):
            return None

        values, self.buffer[key] = self._split_values(self.buffer[key])

        mean, std = self._compute_stats(values)

        return {
            'mean': mean,
            'std': std,
            'time': values[-1]['time'],
            'tags': values[-1]['tags']
        }
