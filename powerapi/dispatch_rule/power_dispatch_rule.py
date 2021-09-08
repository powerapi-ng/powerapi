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
from typing import Tuple
from enum import IntEnum

from powerapi.report import PowerReport

from .dispatch_rule import DispatchRule


class PowerDepthLevel(IntEnum):
    """
    Enumeration that specify which report level use to group by the reports
    """

    TARGET = -1
    SENSOR = 0
    SOCKET = 1
    CORE = 2


def extract_id_from_report(report: PowerReport, depth: PowerDepthLevel) -> Tuple:
    """
    :return: a report id generated from the report and the given depth
    """
    if depth == PowerDepthLevel.TARGET:
        return (report.target,)

    if depth == PowerDepthLevel.SENSOR:
        return (report.sensor,)

    if depth == PowerDepthLevel.SOCKET:
        return extract_id_from_report(report, depth - 1) + (report.metadata['socket'],)

    return extract_id_from_report(report, depth - 1) + (report.metadata['core'],)


class PowerDispatchRule(DispatchRule):
    """
    Group by rule for HWPC report
    """
    def __init__(self, depth: PowerDepthLevel, primary=False):
        """
        :param depth:
        :type depth: HWPCDepthLevel
        """
        DispatchRule.__init__(self, primary)
        self.depth = depth
        self.fields = self._set_field()

    def _set_field(self):
        if self.depth == PowerDepthLevel.TARGET:
            return ['target']

        return ['sensor', 'socket', 'core'][:(self.depth + 1)]

    def get_formula_id(self, report):
        return [extract_id_from_report(report, self.depth)]
