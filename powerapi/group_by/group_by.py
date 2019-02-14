# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


class GroupBy:
    """
    Group by rule
    """
    def __init__(self, primary=False):
        self.is_primary = primary
        self.fields = None

    def extract(self, report):
        """
        divide a report into multiple report given a group_by rule

        :param report:
        :type report: powerapi.report.report.Report
        :rtype: ([(tuple, powerapi.report.report.Report)]) a list all report
                with their identifier
        """
        raise NotImplementedError()
