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
from powerapi.pusher import PusherActor, PusherStartHandler, ReportHandler
from powerapi.pusher import PusherState
from powerapi.actor import Actor, SocketInterface
from powerapi.report import PowerReport
from powerapi.message import StartMessage, OKMessage, ErrorMessage

##############################################################################


def get_fake_db():
    """ Return a fake MongoDB """
    fake_mongo = mock.Mock(stream_mode=False)
    values = [2, 3]

    def fake_next():
        if not values:
            return None
        return values.pop()

    def fake_iter():
        return iter([])

    fake_mongo.__next__ = fake_next
    fake_mongo.__iter__ = fake_iter
    return fake_mongo


def get_fake_socket_interface():
    """ Return a fake SockerInterface """
    return mock.Mock(spec_set=SocketInterface)


##############################################################################


class TestHandlerPusher:
    """ TestHandlerPusher class """

    def test_pusher_start_handler(self):
        """
        Test the StartHandler of PusherActor
        """

        # Define PusherState
        fake_database = get_fake_db()
        fake_socket_interface = get_fake_socket_interface()
        pusher_state = PusherState(Actor._initial_behaviour,
                                   fake_socket_interface,
                                   fake_database,
                                   mock.Mock())
        assert pusher_state.initialized is False

        # Define StartHandler
        start_handler = PusherStartHandler()

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            start_handler.handle(msg, pusher_state)
            assert fake_database.method_calls == []
            assert fake_socket_interface.method_calls == []
            assert pusher_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage(), pusher_state)
        assert pusher_state.initialized is True


    def test_pusher_power_handler(self):
        """
        Test the ReportHandler of PusherActor
        """
        
        # Define PusherState
        fake_database = get_fake_db()
        fake_socket_interface = get_fake_socket_interface()
        pusher_state = PusherState(Actor._initial_behaviour,
                                   fake_socket_interface,
                                   fake_database,
                                   mock.Mock())
        assert pusher_state.initialized is False

        # Define PowerHandler
        power_handler = ReportHandler()
        
        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            power_handler.handle_message(msg, pusher_state)
            assert pusher_state.database.method_calls == []
            assert pusher_state.initialized is False

        pusher_state.initialized = True

        # Test Random message when state is initialized
        #to_send = [OKMessage(), ErrorMessage("Error"),
        #           create_report_root({})]
        #for msg in to_send:
        #    power_handler.handle_message(msg, pusher_state)
        #    assert pusher_state.database.method_calls == []

        ## Test with a PowerMessage
        #for _ in range(101):
        #    power_handler.handle_message(PowerReport("10", "test", "test", "test", "test"),
        #                                 pusher_state)
        #assert len(pusher_state.buffer) == 101
