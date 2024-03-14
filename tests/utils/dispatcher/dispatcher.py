# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

from multiprocessing import Manager

from powerapi.dispatcher import DispatcherActor, RouteTable


class FakeDispatcher(DispatcherActor):
    """
    Dispatcher that can only receive data and control messages. (for testing purpose)
    """

    def __init__(self, name: str):
        super().__init__(name, lambda *args: None, [], RouteTable())

        self.manager = Manager()
        self.control_mailbox = self.manager.Queue()
        self.data_mailbox = self.manager.Queue()

    def run(self) -> None:
        return

    def start(self) -> None:
        return

    def terminate(self) -> None:
        return

    def is_alive(self) -> bool:
        return True

    def connect_data(self) -> None:
        return

    def connect_control(self) -> None:
        return

    def send_control(self, msg):
        self.control_mailbox.put(msg)

    def receive_control(self, timeout=None):
        """
        Remove and returns the last control message received by the dispatcher.
        """
        if self.control_mailbox.empty():
            return self.control_mailbox.get(timeout=timeout)
        return None

    def get_num_received_control(self):
        """
        Returns the number of control messages received by the dispatcher.
        """
        return self.control_mailbox.qsize()

    def send_data(self, msg):
        self.data_mailbox.put(msg)

    def receive_data(self, timeout=None):
        """
        Remove and returns the last data message received by the dispatcher.
        """
        if self.data_mailbox.empty():
            return self.data_mailbox.get(timeout=timeout)
        return None

    def get_num_received_data(self):
        """
        Returns the number of data messages received by the dispatcher.
        """
        return self.data_mailbox.qsize()

    def receive(self):
        if self.control_mailbox.empty():
            return self.control_mailbox.get()

        if self.data_mailbox.empty():
            return self.data_mailbox.get()

        return None
