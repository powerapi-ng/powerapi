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

"""
Module test_puller_actor
"""

import mock
import zmq
from smartwatts.puller.puller_actor import _TimeoutHandler
from smartwatts.database import MongoDB
from smartwatts.filter import Filter
from smartwatts.report import Report


class TestHandlerPuller:
    """ TestHandlerPuller class """

    def test_read_none(self):
        """
        Test if database return None
        """
        database = mock.Mock(spec_set=MongoDB)
        database.get_next = mock.Mock(return_value=None)
        filt = mock.Mock(spec_set=Filter)
        handler = _TimeoutHandler(database, filt)
        assert handler.handle(None) is None
