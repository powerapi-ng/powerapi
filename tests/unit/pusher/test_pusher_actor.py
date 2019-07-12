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

from mock import Mock
from datetime import datetime
from powerapi.report import create_report_root, HWPCReport
from powerapi.report_model import HWPCModel
from powerapi.pusher import PusherStartHandler, ReportHandler
from powerapi.pusher import PusherState, ReportHandler
from powerapi.actor import Actor, SocketInterface
from powerapi.message import StartMessage, OKMessage, ErrorMessage

##############################################################################


def get_fake_db():
    """ Return a fake MongoDB """
    fake_mongo = Mock(stream_mode=False)
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
    return Mock(spec_set=SocketInterface)


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
        pusher_state = PusherState(Mock(),
                                   fake_database,
                                   HWPCModel())
        pusher_state.actor.socket_interface = fake_socket_interface
        assert pusher_state.initialized is False

        # Define StartHandler
        start_handler = PusherStartHandler(pusher_state)

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            start_handler.handle(msg)
            assert fake_database.method_calls == []
            assert fake_socket_interface.method_calls == []
            assert pusher_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage())
        assert pusher_state.initialized is True


    def test_pusher_power_handler(self):
        """
        Test the ReportHandler of PusherActor
        """
        
        # Define PusherState
        fake_database = get_fake_db()
        fake_socket_interface = get_fake_socket_interface()
        pusher_state = PusherState(Mock(),
                                   fake_database,
                                   HWPCModel())
        pusher_state.actor.socket_interface = fake_socket_interface
        assert pusher_state.initialized is False

        # Define PowerHandler
        power_handler = ReportHandler(pusher_state)
        
        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   create_report_root({})]
        for msg in to_send:
            power_handler.handle_message(msg)
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


def test_ReportHandler_message_saving_order():
    """
    Handle 3 HWPCReport with a pusher.ReportHandler
    The maximum size of the handler buffer is 2
    This 3 reports are not sent in their chronological order

    First report : timestamp = 0
    Second report : timestamp = 2
    Third report : timestamp = 1

    When the handler save the received reports test if the reports are saved in
    their chronological order

    """

    fake_database = get_fake_db()
    fake_database.save_many = Mock()

    pusher_state = PusherState(Mock(), fake_database, HWPCModel())
    report_handler = ReportHandler(pusher_state, delay=10000, max_size=2)

    report0 = HWPCReport(datetime.fromtimestamp(0), None, None, None)
    report1 = HWPCReport(datetime.fromtimestamp(2), None, None, None)
    report2 = HWPCReport(datetime.fromtimestamp(1), None, None, None)

    report_handler.handle(report0)
    report_handler.handle(report1)
    report_handler.handle(report2)

    buffer = fake_database.save_many.call_args[0][0]

    assert len(buffer) == 3
    assert buffer[0].timestamp < buffer[1].timestamp
    assert buffer[1].timestamp < buffer[2].timestamp
