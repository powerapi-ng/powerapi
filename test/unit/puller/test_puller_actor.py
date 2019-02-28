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
Module test_actor_puller
"""

import mock
import zmq
from powerapi.puller import PullerState
from powerapi.database import MongoDB
from powerapi.filter import Filter
from powerapi.report import Report, HWPCReport, create_report_root
from powerapi.puller import PullerActor, PullerState
from powerapi.puller import PullerStartHandler
from powerapi.actor import Actor, State, SocketInterface, Supervisor
from powerapi.message import OKMessage, ErrorMessage, StartMessage

#########################################
# Initialization functions
#########################################


class FakeReport(Report):
    """ FakeReport for testing """

    def __init__(self):
        Report.__init__(self, None, None, None)
        self.value = None

    def serialize(self):
        """ Override """
        pass

    def deserialize(self, json):
        """ Override """
        self.value = json
        return self.value


def get_fake_mongodb():
    """ Return a fake MongoDB """
    fake_mongo = mock.Mock(spec_set=MongoDB)
    values = [2, 3]

    def fake_next():
        if not values:
            return None
        return values.pop()

    def fake_iter(_):
        return iter([])

    fake_mongo.__next__ = fake_next
    fake_mongo.__iter__ = fake_iter
    return fake_mongo


def get_fake_filter():
    """
    Return a fake Filter
    .filters    => []
    .route()    => return 10
    .get_type() => return FakeReport
    """
    fake_filter = mock.Mock()
    fake_filter.filters = []
    fake_filter.route = mock.Mock(return_value=mock.Mock())
    fake_filter.get_type = mock.Mock(return_value=FakeReport)
    return fake_filter


def get_fake_socket_interface():
    """ Return a fake SockerInterface """
    return mock.Mock(spec_set=SocketInterface)


#########################################


class TestPullerActor:
    """ TestPullerActor class """

    def test_no_stream(self):
        """ Test if the actor kill himself after reading db """
        puller = PullerActor("puller_mongo", get_fake_mongodb(),
                             get_fake_filter(), 0, stream_mode=False)
        supervisor = Supervisor()
        supervisor.launch_actor(puller)
        puller.join()
        assert puller.is_alive() is False


class TestHandlerPuller:
    """ TestHandlerPuller class """

    def test_puller_start_handler(self):
        """
        Test the StartHandler of PullerActor
        """

        # Define PullerState
        fake_database = get_fake_mongodb()
        fake_socket_interface = get_fake_socket_interface()
        fake_filter = get_fake_filter()
        puller_state = PullerState(Actor._initial_behaviour,
                                   fake_socket_interface,
                                   mock.Mock(),
                                   fake_database,
                                   fake_filter,
                                   False)
        assert puller_state.initialized is False

        # Define StartHandler
        start_handler = PullerStartHandler()

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            start_handler.handle(msg, puller_state)
            assert fake_database.method_calls == []
            assert fake_socket_interface.method_calls == []
            assert fake_filter.method_calls == []
            assert puller_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage(), puller_state)
        assert puller_state.initialized is True
