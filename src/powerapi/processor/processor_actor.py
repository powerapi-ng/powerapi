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
import logging

from powerapi.actor import State, Actor
from powerapi.handler import PoisonPillMessageHandler
from powerapi.message import PoisonPillMessage


class ProcessorState(State):
    """
    Processor Actor State

    Contains in addition to State values :
      - the targets actors
    """

    def __init__(self, actor: Actor, target_actors: list, target_actors_names: list):
        """
        :param list target_actors: List of target actors for the processor
        """
        super().__init__(actor)

        if not target_actors:
            target_actors = []

        self.target_actors = target_actors
        self.target_actors_names = target_actors_names


class ProcessorActor(Actor):
    """
    ProcessorActor class

    A processor modifies a report and sends the modified report to a list of targets
    actor.
    """

    def __init__(self, name: str, level_logger: int = logging.WARNING, timeout: int = 5000):
        Actor.__init__(self, name, level_logger, timeout)
        self.state = ProcessorState(actor=self, target_actors=[], target_actors_names=[])

    def setup(self):
        """
        Define PoisonPillMessage handler
        """
        self.add_handler(message_type=PoisonPillMessage, handler=PoisonPillMessageHandler(state=self.state))

    def add_target_actor(self, actor: Actor):
        """
        Add the given actor to the list of targets
        :param actor: Actor to be defined as target
        """
        self.state.target_actors.append(actor)
