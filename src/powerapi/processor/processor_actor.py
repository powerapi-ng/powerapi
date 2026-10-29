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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from powerapi.actor.actor import Actor
from powerapi.actor.handler import PoisonPillMessageHandler, StartMessageHandler
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.actor.state import State
from powerapi.processor.handlers import ProcessorReportHandler

if TYPE_CHECKING:
    from powerapi.actor import ActorProxy
    from powerapi.processor.processor import Processor


class ProcessorState(State):
    """
    Adapt a processing component lifecycle to actor execution.
    """

    def __init__(self, actor: ProcessorActor, processor: Processor):
        """
        Store the processor and actor without acquiring resources.
        :param actor: Actor executing the processor
        :param processor: Processing component owned by this state
        """
        super().__init__(actor)

        self.processor = processor

    def initialize(self) -> None:
        """
        Connect targets and initialize the processor.
        """
        for target in self.actor.target_actors:
            target.connect_data()

        self.processor.initialize()
        for report_processor in self.processor.get_report_processors():
            self.actor.add_handler(report_processor.report_type, ProcessorReportHandler(self, report_processor))

    def teardown(self) -> None:
        """
        Release processor resources and disconnect targets.
        """
        try:
            self.processor.teardown()
        finally:
            for target in self.actor.target_actors:
                target.disconnect()


class ProcessorActor(Actor):
    """
    Process reports and forward results to target actors.
    """
    state: ProcessorState

    def __init__(self, name: str, processor: Processor, level_logger: int = logging.WARNING):
        """
        Initialize a new processor actor.
        :param name: Name of the processor actor
        :param processor: Processing component executed by the actor
        :param level_logger: Logging level of the actor
        """
        super().__init__(name, level_logger)

        self.target_actors: list[ActorProxy] = []
        self.processor = processor

    def setup(self) -> None:
        """
        Register lifecycle handlers; report handlers are bound during initialization.
        """
        self.state = ProcessorState(self, self.processor)

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))

    def add_target_actor(self, actor: ActorProxy) -> None:
        """
        Add the given actor to the list of targets.
        :param actor: Actor to be defined as target
        """
        self.target_actors.append(actor)


class PreProcessorActor(ProcessorActor):
    """
    Process reports from pullers before forwarding them to a formula.
    """


class PostProcessorActor(ProcessorActor):
    """
    Process reports from a formula before forwarding them to pushers.
    """
