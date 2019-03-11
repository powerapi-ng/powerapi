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

from enum import IntEnum

from powerapi.dispatch_rule import DispatchRule


class HWPCDepthLevel(IntEnum):
    """
    Enumeration that specify which report level use to group by the reports
    """

    TARGET = -1
    ROOT = 0
    SOCKET = 1
    CORE = 2


class HWPCDispatchRule(DispatchRule):
    """
    Group by rule for HWPC report
    """
    def __init__(self, depth, primary=False):
        """
        :param depth:
        :type depth: HWPCDepthLevel
        """
        DispatchRule.__init__(self, primary)
        self.depth = depth
        self.fields = self._set_field()

    def _set_field(self):
        if self.depth == HWPCDepthLevel.TARGET:
            return ['target']

        return ['sensor', 'socket', 'core'][:(self.depth + 1)]

    def get_formula_id(self, report):
        """
        See :meth:`DispatchRule.extract <powerapi.dispatch_rule.abstract_dispatch_rule.DispatchRule.extract>`
        """
        if self.depth == HWPCDepthLevel.TARGET:
            return [(report.target,)]

        if self.depth == HWPCDepthLevel.ROOT:
            return [(report.sensor,)]

        non_shared_group = _extract_non_shared_group(report)

        if self.depth == HWPCDepthLevel.SOCKET:
            id_list = []
            for socket_report in non_shared_group.items():
                id_list.append((report.sensor, socket_report[0]))
            return id_list

        if self.depth == HWPCDepthLevel.CORE:
            id_list = []
            for socket_report in non_shared_group.items():
                for core_report in socket_report[1].items():
                    id_list.append((report.sensor, socket_report[0],
                                    core_report[0]))
            return id_list

        return []


def _number_of_core_per_socket(group):
    """
    Compute the number of core per socket in this group
    :param group: group must be a valide group (composed by socket, core, event)
    :type group: Dict
    :rtype: int : the number of core per socket in this group
    """
    return len(list(group.values())[0])


def _extract_non_shared_group(report):
    """
    extract a non shared group form the given report.
    A shared group is a group that contains events that are shared between
    multiple cores (like RAPL or PCU)

    :rtype:{str:HWPCReportSocket}: a group containing ReportSocket
    """
    biggest_group = None
    maximum_number_of_core = -1
    for _, group in report.groups.items():
        number_of_core = _number_of_core_per_socket(group)
        if number_of_core > maximum_number_of_core:
            maximum_number_of_core = number_of_core
            biggest_group = group
    return biggest_group
