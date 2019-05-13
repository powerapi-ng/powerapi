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


class HandlerException(Exception):
    """
    Exception raised when a problem appear in a handler
    """
    def __init__(self, msg):
        """
        :param str msg: Message of the error
        """
        super().__init__(msg)


class Handler:
    """
    Class that handle a message of a given type
    """
    def __init__(self, state):
        """
        :param state: Actor state
        """
        self.state = state

    def handle_message(self, msg):
        """
        Handle a message and return a the new state value of the actor

        This is the method that should be called to handle received message
        this method call :meth:`Handler.handle <powerapi.handler.abstract_handler.Handler.handle>`

        :param Object msg: the message received by the actor
        """
        self.handle(msg)

    def handle(self, msg):
        """
        Handle a message and return a the new state value of the actor

        Override this method to implement the handler behaviour

        :param Object msg: the message received by the actor
        """
        raise NotImplementedError()


class InitHandler(Handler):
    """
    Class that handle a message of a given type if the actor is initialized
    """

    def handle_message(self, msg):
        """
        Handle a message and return a the new state value of the actor

        This is the method that should be called to handle received message

        if the given state is not initialized, return the given state without
        side effect. Otherwise, use the
        :meth:`Handler.handle <powerapi.handler.abstract_handler.Handler.handle>`
        method to handle the message

        :param Object msg: the message received by the actor
        """
        if not self.state.initialized:
            return

        self.handle(msg)
