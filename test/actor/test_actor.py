import multiprocessing


import setproctitle
import pytest

from mock import Mock, patch

from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage
from smartwatts.actor import Actor, State
from smartwatts.handler import PoisonPillMessageHandler


class DummyActor(Actor):

    def __init__(self, name='dummy_actor', verbose=False):
        Actor.__init__(self, name, verbose=verbose)
        self.state = State(Mock(), Mock())

    def setup(self):
        Actor.setup(self)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())


ACTOR_NAME = 'dummy_actor'
VERBOSE_MODE = False



@pytest.fixture()
def dummy_actor():
    """ Return a dummy actor"""
    actor = DummyActor(name=ACTOR_NAME, verbose=VERBOSE_MODE)
    actor._signal_handler_setup = Mock()
    return actor


@pytest.fixture()
def initialized_dummy_actor(dummy_actor):
    """ return an initialized dummy actor """
    dummy_actor.setup()
    return dummy_actor


def test_actor_initialisation(dummy_actor):
    """ test actor attributes initialization"""
    assert dummy_actor.state.alive is True


def test_setup(dummy_actor):
    """test if the socket interface and the signal handler are correctly
    initialized and if the proc title is correctly set after the run function
    was call

    """
    dummy_actor.setup()

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
        initialized_dummy_actor.get_corresponding_handler('toto')


def test_get_handler(initialized_dummy_actor):
    """ Test to get the predefined handler for PoisonPillMessage type
    """
    handler = initialized_dummy_actor.get_corresponding_handler(
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
