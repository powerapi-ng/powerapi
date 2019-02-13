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


class UnknowMessageTypeException(Exception):
    """
    Exception happen when we don't know the message type
    """

class Message:
    """
    Abstract class message. Each object that is used by zmq
    need to be a Message.
    """
    def __repr__(self):
        raise NotImplementedError()


class PoisonPillMessage(Message):
    """
    Message which allow to kill an actor
    """
    def __repr__(self):
        return "PoisonPillMessage"


class StartMessage(Message):
    """
    Message that ask the actor to launch its initialisation process
    """
    def __repr__(self):
        return "StartMessage"


class OKMessage(Message):
    """
    Message used in synchron communication to answer that the actor
    completed the task previously asked
    """
    def __repr__(self):
        return "OKMessage"


class ErrorMessage(Message):
    """
    Message used to indicate that an error as occuried
    """

    def __init__(self, error_message):
        """
        :param str error_code: message associated to the error
        """
        self.error_message = error_message

    def __repr__(self):
        return "ErrorMessage"
