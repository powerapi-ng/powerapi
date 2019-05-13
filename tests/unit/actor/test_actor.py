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

import logging
import pytest
from mock import Mock
import setproctitle

from powerapi.message import UnknowMessageTypeException, PoisonPillMessage
from powerapi.actor import Actor, State
from powerapi.handler import PoisonPillMessageHandler


ACTOR_NAME = "dummy_actor"
LOG_LEVEL = logging.NOTSET

class DummyActor(Actor):

    def __init__(self, name=ACTOR_NAME):
        Actor.__init__(self, name, level_logger=LOG_LEVEL)

    def setup(self):
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))


@pytest.fixture()
def dummy_actor_mocked():
    """ Return a mocked dummy actor"""
    actor = DummyActor()
    actor._signal_handler_setup = Mock()
    actor.state = Mock()
    actor.socket_interface = Mock()
    return actor


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


def test_setup(dummy_actor_mocked):
    """
    Test if the socket interface and the signal handler are correctly
    initialized and if the proc title is correctly set after the run function
    was call
    """
    dummy_actor_mocked._setup()

    assert setproctitle.getproctitle() == ACTOR_NAME
    assert len(dummy_actor_mocked.socket_interface.setup.mock_calls) == 1
    assert len(dummy_actor_mocked._signal_handler_setup.mock_calls) == 1
    dummy_actor_mocked._kill_process()


def test_kill_process(dummy_actor_mocked):
    """
    Check if the kill_process close the socket_interface
    """
    dummy_actor_mocked.setup()
    dummy_actor_mocked._kill_process()
    assert len(dummy_actor_mocked.socket_interface.close.mock_calls) == 1


def test_get_handler_unknow_message_type(initialized_dummy_actor):
    """
    Test to handle a message with no handle bind to its type

    must raise an UnknowMessageTypeException
    """
    with pytest.raises(UnknowMessageTypeException):
        initialized_dummy_actor.state.get_corresponding_handler('toto')


def test_get_handler(initialized_dummy_actor):
    """
    Test to get the predefined handler for PoisonPillMessage type
    """
    handler = initialized_dummy_actor.state.get_corresponding_handler(
        PoisonPillMessage())
    assert isinstance(handler, PoisonPillMessageHandler)


def test_behaviour_change(initialized_dummy_actor):
    """
    Test if the actor behaviour could be change during the current
    behaviour function execution
    """
    buzzer = Mock()

    def next_behaviour(actor):
        """ call the buzzer and set the alive flag to False"""
        buzzer.buzz()
        actor.state.alive = False

    def init_behaviour(actor):
        actor.set_behaviour(next_behaviour)

    initialized_dummy_actor.set_behaviour(init_behaviour)
    initialized_dummy_actor.run()

    assert len(buzzer.mock_calls) == 1
