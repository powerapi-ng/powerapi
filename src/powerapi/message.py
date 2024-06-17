# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
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

class Message:
    """
    Base Message class.
    """

    def __init__(self, sender_name: str):
        """
        :param sender_name: Name of the sender
        """
        self.sender_name = sender_name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.sender_name})"


class OKMessage(Message):
    """
    Message sent by actors when it had been successfully initialized.
    """

    def __init__(self, sender_name: str):
        """
        :param sender_name: Name of the sender
        """
        super().__init__(sender_name)


class ErrorMessage(Message):
    """
    Message sent by actors when an error occurs during initialization.
    """

    def __init__(self, sender_name: str, error_message: str):
        """
        :param sender_name: Name of the sender
        :param error_message: Error message
        """
        super().__init__(sender_name)
        self.error_message = error_message


class StartMessage(Message):
    """
    Message that asks the actor to launch its initialization process.
    """

    def __init__(self, sender_name: str):
        super().__init__(sender_name)


class PoisonPillMessage(Message):
    """
    Message that asks the actor to launch its teardown process.
    """

    def __init__(self, sender_name: str, soft_kill: bool = True):
        """
        :param sender_name: Name of the sender
        :param soft_kill: Whether to use a soft or hard kill
        """
        super().__init__(sender_name)
        self.is_soft = soft_kill

    def __eq__(self, other) -> bool:
        if isinstance(other, PoisonPillMessage):
            return self.sender_name == other.sender_name and other.is_soft == self.is_soft
        return False
