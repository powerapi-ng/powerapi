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

import logging
import multiprocessing
import pytest
import setproctitle

from mock import Mock, patch

from powerapi.message import UnknowMessageTypeException, PoisonPillMessage
from powerapi.actor import Actor, State
from powerapi.handler import PoisonPillMessageHandler


ACTOR_NAME = "dummy_actor"

class DummyActor(Actor):

    def __init__(self, name=ACTOR_NAME):
        Actor.__init__(self, name)
        self.state = State(Mock(), Mock())

    def setup(self):
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())


@pytest.fixture()
def dummy_actor():
    """ Return a dummy actor"""
    actor = DummyActor()
    actor._signal_handler_setup = Mock()
    return actor


@pytest.fixture()
def initialized_dummy_actor(dummy_actor):
    """ return an initialized dummy actor """
    dummy_actor._setup()
    return dummy_actor


def test_actor_initialisation(dummy_actor):
    """ test actor attributes initialization"""
    assert dummy_actor.state.alive is True


def test_setup(dummy_actor):
    """test if the socket interface and the signal handler are correctly
    initialized and if the proc title is correctly set after the run function
    was call

    """
    dummy_actor._setup()

    assert setproctitle.getproctitle() == ACTOR_NAME
    assert len(dummy_actor.state.socket_interface.setup.mock_calls) == 1
    assert len(dummy_actor._signal_handler_setup.mock_calls) == 1
    dummy_actor._kill_process()


def test_kill_process(dummy_actor):
    """ check if the kill_process close the socket_interface
    """
    dummy_actor.setup()

    dummy_actor._kill_process()
    assert len(dummy_actor.state.socket_interface.close.mock_calls) == 1


def test_get_handler_unknow_message_type(initialized_dummy_actor):
    """test to handle a message with no handle bind to its type

    must raise an UnknowMessageTypeException

    """
    with pytest.raises(UnknowMessageTypeException):
        initialized_dummy_actor.state.get_corresponding_handler('toto')


def test_get_handler(initialized_dummy_actor):
    """ Test to get the predefined handler for PoisonPillMessage type
    """
    handler = initialized_dummy_actor.state.get_corresponding_handler(
        PoisonPillMessage())
    assert isinstance(handler, PoisonPillMessageHandler)


def test_behaviour_change(initialized_dummy_actor):
    """ Test if the actor behaviour could be change during the current
    behaviour function execution
    """

    buzzer = Mock()

    def next_behaviour(actor):
        """ call the buzzer and set the alive flag to False"""
        buzzer.buzz()
        actor.state.alive = False

    def init_behaviour(actor):
        actor.state.behaviour = next_behaviour

    initialized_dummy_actor.state.behaviour = init_behaviour

    initialized_dummy_actor.run()

    assert len(buzzer.mock_calls) == 1
