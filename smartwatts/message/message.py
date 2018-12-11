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
Module message
"""


class UnknowMessageTypeException(Exception):
    """
    Exception happen when we don't know the message type
    """


class PoisonPillMessage:
    """
    Class of message which allow to kill an actor
    """


class StartMessage:
    """ Message that ask the actor to launch its initialisation process
    """


class OKMessage:
    """ Message used in synchrone communication to answer that the actor
    completed the task previously asked
    """


class ErrorMessage:
    """ Message used to indicate that an error as occuried

    encapsulated error code :
        -
    """

    def __init__(self, error_code):
        self.error_code = error_code
