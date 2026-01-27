# Copyright (c) 2023, Inria
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
from typing import TYPE_CHECKING

from powerapi.actor import Actor

if TYPE_CHECKING:
    from powerapi.actor import ActorProxy


class ProcessorActor(Actor):
    """
    Processor actor class.
    Used to process reports before sending them to target actor(s).
    """

    def __init__(self, name: str, level_logger: int = logging.WARNING, timeout: int = 5000):
        """
        Initializes a new processor actor.
        :param name: Name of the processor actor
        :param level_logger: Logging level of the actor
        :param timeout: Timeout in milliseconds
        """
        super().__init__(name, level_logger, timeout)

        self.target_actors: list[ActorProxy] = []

    def add_target_actor(self, actor: ActorProxy) -> None:
        """
        Add the given actor to the list of targets.
        :param actor: Actor to be defined as target
        """
        self.target_actors.append(actor)


class PreProcessorActor(ProcessorActor):
    """
    Pre-Processor actor class.
    Used to process reports coming from puller(s) before sending them to a formula.
    """


class PostProcessorActor(ProcessorActor):
    """
    Post-Processor actor class.
    Used to process reports produced by a formula before sending them to pusher(s).
    """
