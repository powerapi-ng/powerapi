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


class UnknowMessageTypeException(Exception):
    """
    Exception happen when we don't know the message type
    """


class Message:
    """
    Abstract class message. Each object that is used by zmq
    need to be a Message.
    """
    def __str__(self):
        raise NotImplementedError()


class PoisonPillMessage(Message):
    """
    Message which allow to kill an actor
    """
    def __str__(self):
        return "PoisonPillMessage"


class StartMessage(Message):
    """
    Message that ask the actor to launch its initialisation process
    """
    def __str__(self):
        return "StartMessage"


class OKMessage(Message):
    """
    Message used in synchron communication to answer that the actor
    completed the task previously asked
    """
    def __str__(self):
        return "OKMessage"


class ErrorMessage(Message):
    """
    Message used to indicate that an error as occuried
    """

    def __init__(self, error_message):
        """
        :param str error_code: message associated to the error
        """
        self.error_message = error_message

    def __str__(self):
        return "ErrorMessage"
