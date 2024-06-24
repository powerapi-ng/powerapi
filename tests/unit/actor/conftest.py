# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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

import pytest
from copy import copy
from powerapi.actor import SocketInterface


@pytest.fixture()
def socket_interface():
    """
    Return a socket interface that haven't been initialized.
    """
    yield SocketInterface('test-socket-interface')


@pytest.fixture()
def bound_socket_interface(socket_interface):
    """
    Return a socket interface that have been bound.
    This is equivalent to the socket interface that will be used by an actor to receive messages.
    """
    socket_interface.bind()
    yield socket_interface
    socket_interface.unbind()


@pytest.fixture()
def connected_socket_interface(socket_interface):
    """
    Return a socket interface that have been connected to its corresponding bound sockets.
    This is equivalent to the socket interface used to send messages to a specific actor.
    """

    # Copy the bound socket interface and remove the sockets.
    # This is necessary to reproduce how the socket interface will be used by the actors.
    # Because the bounded socket interface live in another `Process` and only its actor can access it.
    # Other actors have an empty socket interface that needs to be connected to be usable.
    socket_interface_copy = copy(socket_interface)
    socket_interface_copy.control_socket = None
    socket_interface_copy.data_socket = None

    socket_interface_copy.connect()
    yield socket_interface_copy
    socket_interface_copy.disconnect()
