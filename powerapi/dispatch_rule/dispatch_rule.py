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


class DispatchRule:
    """
    Group by rule
    """
    def __init__(self, primary=False):
        self.is_primary = primary
        self.fields = None

    def get_formula_id(self, report):
        """
        return id of the formulas that the receive report must be send

        :param report:
        :type report: powerapi.report.report.Report
        :rtype: ([tuple]) a list formula identifier
        """
        raise NotImplementedError()
