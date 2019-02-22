import pytest


import zmq
from mock import Mock 
from powerapi.actor import Actor, Supervisor, ActorInitError, State
from powerapi.actor import SocketInterface, ActorAlreadySupervisedException
from powerapi.message import OKMessage, ErrorMessage, StartMessage

#########
# Utils #
#########

class FakeActor(Actor):

    def __init__(self):
        Actor.__init__(self, 'test_supervisor')
        self.state = State(Mock(), SocketInterface('test_supervisor', 0), Mock())
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
        return OKMessage()


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
        return ErrorMessage('error')

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
def test_launch_actor(supervisor):
    """
    Create a supervisor and launch a FakeActor

    test to launch this actor when the supervisor already supervise another
    actor and when it supervise no actors

    Test if :
      - the size of the supervised actor list increaed by one
      - the new actor was append to the list
    """
    list_length = len(supervisor.supervised_actors)
    actor = FakeActor()
    supervisor.launch_actor(actor, start_message=False)
    assert len(supervisor.supervised_actors) == list_length + 1
    assert actor in supervisor.supervised_actors


def test_launch_actor_start_message(supervisor):
    """
    Create a supervisor and launch a FakeActor with a StartMessage

    test to launch this actor when the supervisor already supervise another
    actor and when it supervise no actors

    Test if :
      - the size of the supervised actor list is increase by one
      - the new actor was append to the list
      - the new actor has receive a StartMessage
    """
    list_length = len(supervisor.supervised_actors)
    actor = FakeActor()
    supervisor.launch_actor(actor)
    assert len(supervisor.supervised_actors) == list_length + 1
    assert actor in supervisor.supervised_actors
    assert len(actor.send_msg) == 1
    assert isinstance(actor.send_msg.pop(), StartMessage)

def test_launch_actor_connect_error(supervisor):
    """
    Create a supervisor and launch a FakeActorConnectionError

    Test if:
      - the size of the supervised actor list didn't increase
      - an zmq.error.ZMQError is raise
    """
    list_length = len(supervisor.supervised_actors)
    actor = FakeActorConnectError()
    with pytest.raises(zmq.error.ZMQError):
        supervisor.launch_actor(actor)
    assert len(supervisor.supervised_actors) == list_length

def test_launch_actor_init_error(supervisor):
    """
    Create a supervisor and launch a FakeActorInitError

    Test if:
      - the size of the supervised actor list didn't increase
      - an powerapi.actor.ActorInitError is raise
    """
    list_length = len(supervisor.supervised_actors)
    actor = FakeActorInitError()
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(actor)
    assert len(supervisor.supervised_actors) == list_length


############
# TEST ADD #
############
# def test_add_actor(supervisor):
#     """
#     create a supervisor and add it an actor when the list of supervised actors
#     is empty or contain already one actor

#     Test if:
#       - the size of the supervised actor list is increase by one
#       - the new actor's context is the supervisor context
#       - the new actor was append to the list
#     """
#     list_length = len(supervisor.supervised_actors)
#     actor = FakeActor()
#     supervisor.add_actor(actor)
#     assert len(supervisor.supervised_actors) == list_length + 1
#     assert actor in supervisor.supervised_actors
#     assert actor.state.socket_interface.context == supervisor.context


# def test_add_actor_already_supervised(supervisor):
#     """
#     create a supervisor that supervise one actor. Try to re-add this actor

#     Test if:
#       - the supervisor raise an ActorAltreadySupervisedException
#       - the size of the supervised actor list didn't increase
#     """
#     actor = FakeActor()
#     supervisor.add_actor(actor)

#     list_length = len(supervisor.supervised_actors)
#     with pytest.raises(ActorAlreadySupervisedException):
#         supervisor.add_actor(actor)
#     assert len(supervisor.supervised_actors) == list_length

#############
# TEST KILL #
#############
def test_kill_actor(supervisor):
    """
    create a supervisor and kill its actors. The list of supervised actors
    is empty or contain already one actor

    Test if:
      - all actor in the supervised list are dead
    """
    supervisor.kill_actors()

    for actor in supervisor.supervised_actors:
        assert not actor.is_alive()
