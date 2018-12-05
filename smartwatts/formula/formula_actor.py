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

""" Class that generalize formula behaviour """

from smartwatts.actor import Actor
from smartwatts.report import PowerReport


class FormulaActor(Actor):
    """
    Generalize formula behaviour
    """

    def __init__(self, name, actor_pusher, verbose=False, timeout=None):
        """
        Parameters:
        """
        Actor.__init__(self, name, verbose)
        self.actor_pusher = actor_pusher

    def setup(self):
        self.actor_pusher.connect(self.context)
