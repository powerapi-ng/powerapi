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

import mock
from powerapi.report import Report, create_report_root
from powerapi.puller import PullerActor, PullerState
from powerapi.puller import PullerStartHandler
from powerapi.actor import SocketInterface, Supervisor
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


def get_fake_db():
    """ Return a fake DB """
    fake_mongo = mock.Mock(stream_mode=False)
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
        puller = PullerActor("puller_mongo", get_fake_db(),
                             get_fake_filter(), 0)
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
        fake_database = get_fake_db()
        fake_socket_interface = get_fake_socket_interface()
        fake_filter = get_fake_filter()
        puller_state = PullerState(mock.Mock(),
                                   fake_database,
                                   fake_filter)

        assert puller_state.initialized is False

        # Define StartHandler
        start_handler = PullerStartHandler(puller_state)

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            start_handler.handle(msg)
            assert fake_database.method_calls == []
            assert fake_socket_interface.method_calls == []
            assert fake_filter.method_calls == []
            assert puller_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage())
        assert puller_state.initialized is True
