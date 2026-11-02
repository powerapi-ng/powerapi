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
    from collections.abc import Iterable

    from powerapi.actor import ActorProxy
    from powerapi.processor.processor import Processor


class ProcessorState(State):
    """
    Adapt processing component lifecycles to actor execution.
    """

    def __init__(self, actor: ProcessorActor, processors: Iterable[Processor]):
        """
        Store the processors and actor without acquiring resources.
        :param actor: Actor executing the processor
        :param processors: Processing components in execution order
        """
        super().__init__(actor)

        self.processors = tuple(processors)
        self._initialized_processors: list[Processor] = []

    def initialize(self) -> None:
        """
        Connect targets, initialize processors, and register ordered report chains.
        """
        for target in self.actor.target_actors:
            target.connect_data()

        processors_by_type = {}
        for processor in self.processors:
            processor.initialize()
            self._initialized_processors.append(processor)
            for report_processor in processor.get_report_processors():
                processors_by_type.setdefault(report_processor.report_type, []).append(report_processor)

        for report_type, report_processors in processors_by_type.items():
            self.actor.add_handler(report_type, ProcessorReportHandler(self, report_processors))

    def teardown(self) -> None:
        """
        Release processor resources and disconnect targets.
        """
        try:
            for processor in reversed(self._initialized_processors):
                processor.teardown()
        finally:
            for target in self.actor.target_actors:
                target.disconnect()


class ProcessorActor(Actor):
    """
    Process reports and forward results to target actors.
    """
    state: ProcessorState

    def __init__(self, name: str, processors: Iterable[Processor], level_logger: int = logging.WARNING):
        """
        Initialize a new processor actor.
        :param name: Name of the processor actor
        :param processors: Processing components in execution order
        :param level_logger: Logging level of the actor
        """
        super().__init__(name, level_logger)

        self.target_actors: list[ActorProxy] = []
        self.processors = tuple(processors)

    def setup(self) -> None:
        """
        Register lifecycle handlers; report handlers are bound during initialization.
        """
        self.state = ProcessorState(self, self.processors)

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
