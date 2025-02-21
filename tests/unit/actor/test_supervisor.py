# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest
import zmq
from unittest.mock import Mock
from powerapi.actor import Actor, Supervisor, ActorInitError, State
from powerapi.message import OKMessage, ErrorMessage, StartMessage


#########
# Utils #
#########

class FakeActor(Actor):

    def __init__(self):
        Actor.__init__(self, 'test_supervisor')
        self.state = State(Mock())
        self.send_msg = []
        self.alive = False

    def is_alive(self):
        return self.alive

    def kill(self):
        self.alive = False

    def join(self):
        pass

    def start(self):
        self.alive = True

    def connect_control(self):
        pass

    def connect_data(self):
        pass

    def send_control(self, msg):
        self.send_msg.append(msg)

    def receive_control(self, timeout=None):
        return OKMessage("FakeActor")


class FakeActorConnectError(FakeActor):
    """
    FakeActor that raise an error when trying to connect to it
    """

    def connect_control(self):
        raise zmq.error.ZMQError()


class FakeActorInitError(FakeActor):
    """
    FakeActor that raise an error when trying to initialize it
    """

    def receive_control(self, timeout=None):
        return ErrorMessage('error', 'FakeActorConnectError')


############
# Fixtures #
############
@pytest.fixture(params=[[], [FakeActor()]])
def supervisor(request):
    """
    return a supervisor
    """
    supervisor = Supervisor()
    supervisor.actor_list = request.param
    yield supervisor


###############
# TEST LAUNCH #
###############

def test_launch_actor_increase_supervisor_supervised_actor_list_by_one(supervisor):
    list_length = len(supervisor.supervised_actors)
    actor = FakeActor()
    supervisor.launch_actor(actor, start_message=False)
    assert len(supervisor.supervised_actors) == list_length + 1


def test_launch_actor_put_actor_in_supervisor_supervised_actor_list(supervisor):
    actor = FakeActor()
    supervisor.launch_actor(actor, start_message=False)
    assert actor in supervisor.supervised_actors


def test_launch_actor_send_to_it_a_start_message(supervisor):
    actor = FakeActor()
    supervisor.launch_actor(actor)
    assert len(actor.send_msg) == 1
    msg = actor.send_msg.pop()
    assert isinstance(msg, StartMessage)


def test_launch_an_actor_that_crash_dont_increase_supervised_actor_list(supervisor):
    list_length = len(supervisor.supervised_actors)
    actor = FakeActorConnectError()

    with pytest.raises(zmq.error.ZMQError):
        supervisor.launch_actor(actor)

    assert len(supervisor.supervised_actors) == list_length


def test_launch_an_actor_that_crash_with_ZMQError_raise_ZMQError_exception(supervisor):
    actor = FakeActorConnectError()
    with pytest.raises(zmq.error.ZMQError):
        supervisor.launch_actor(actor)


def test_launch_an_actor_that_crash_with_ActorInitError_raise_ActorInitError_exception(supervisor):
    actor = FakeActorInitError()
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(actor)


#############
# TEST KILL #
#############
def test_kill_actors_methods_all_actor_in_supervised_list_not_alive(supervisor):
    supervisor.kill_actors()
    for actor in supervisor.supervised_actors:
        assert not actor.is_alive()
