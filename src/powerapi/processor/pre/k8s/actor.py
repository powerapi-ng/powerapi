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
from multiprocessing import Manager

from powerapi.actor import Actor, State
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.report import HWPCReport

from .handlers import (
    ActorPoisonPillMessageHandler,
    ActorStartMessageHandler,
    HWPCReportHandler,
)
from .metadata_registry import KubernetesMetadataRegistry
from .monitor_agent import KubernetesMonitorAgent, KubernetesMonitorConfig


class KubernetesProcessorState(State):
    """
    State of the Kubernetes processor actor.
    """

    def __init__(self, actor: Actor, monitor_config: KubernetesMonitorConfig):
        """
        Initializes a Kubernetes pre-processor state.
        """
        super().__init__(actor)

        self.manager = Manager()
        self.metadata_registry = KubernetesMetadataRegistry(self.manager)
        self.monitor_agent = KubernetesMonitorAgent(self.metadata_registry, monitor_config)


class KubernetesPreProcessorActor(ProcessorActor):
    """
    Pre-Processor Actor that adds Kubernetes related metadata to reports.
    """

    def __init__(self, name: str, monitor_config: KubernetesMonitorConfig, level_logger: int = logging.WARNING):
        """
        Initializes a Kubernetes pre-processor actor.
        :param name: The name of the actor
        :param monitor_config: Configuration of the monitoring agent
        :param level_logger: logging level of the actor
        """
        super().__init__(name, level_logger, 5000)

        self.monitor_config = monitor_config

    def setup(self):
        """
        Set up the Kubernetes pre-processor actor.
        """
        self.state = KubernetesProcessorState(self, self.monitor_config)

        self.add_handler(StartMessage, ActorStartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, ActorPoisonPillMessageHandler(self.state))
        self.add_handler(HWPCReport, HWPCReportHandler(self.state))
