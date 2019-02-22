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

from multiprocessing import current_process
import zmq


class SafeContext():
    """
    A context that is bind to a process
    """
    #: (zmq.Context): global process context
    _context = None

    #: (int): pid of the process which this context is bind
    _current_pid = current_process().pid

    @classmethod
    def get_context(cls):
        """
        Return the context of current process
        :return zmq.Context: the context of current process
        """

        if cls._context is None or cls._current_pid != current_process().pid:
            cls._context = zmq.Context()
            cls._current_pid = current_process().pid

        return cls._context
