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
from dataclasses import dataclass
from multiprocessing import Manager

from powerapi.actor import Actor, State
from powerapi.actor.message import StartMessage, PoisonPillMessage
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.report import HWPCReport
from .handlers import K8sPreProcessorActorHWPCReportHandler
from .handlers import K8sPreProcessorActorStartMessageHandler, K8sPreProcessorActorPoisonPillMessageHandler
from .metadata_cache_manager import K8sMetadataCacheManager
from .monitor_agent import K8sMonitorAgent


@dataclass
class K8sProcessorConfig:
    """
    Kubernetes processor actor configuration.
    :param api_mode: Kubernetes API mode (manual, local, cluster)
    :param api_host: Kubernetes API host to connect to
    :param api_key: Kubernetes API key (Bearer Token) to authenticate with
    """
    api_mode: str | None = None
    api_host: str | None = None
    api_key: str | None = None


class K8sProcessorState(State):
    """
    State of the Kubernetes processor actor.
    """

    def __init__(self, actor: Actor, config: K8sProcessorConfig):
        """
        Initializes a Kubernetes pre-processor state.
        """
        super().__init__(actor)

        self.manager = Manager()
        self.metadata_cache_manager = K8sMetadataCacheManager(self.manager)
        self.monitor_agent = K8sMonitorAgent(self.metadata_cache_manager, config.api_mode, config.api_host, config.api_key)


class K8sPreProcessorActor(ProcessorActor):
    """
    Pre-Processor Actor that adds Kubernetes related metadata to reports.
    """

    def __init__(self, name: str, config: K8sProcessorConfig, level_logger: int = logging.WARNING, timeout: int = 5000):
        """
        Initializes a Kubernetes pre-processor actor.
        :param name: The name of the actor
        :param config: Configuration of the actor
        :param level_logger: logging level of the actor
        :param timeout: timeout in seconds
        """
        super().__init__(name, level_logger, timeout)

        self.config = config

    def setup(self):
        """
        Set up the Kubernetes pre-processor actor.
        """
        self.state = K8sProcessorState(self, self.config)

        self.add_handler(StartMessage, K8sPreProcessorActorStartMessageHandler(self.state))
        self.add_handler(HWPCReport, K8sPreProcessorActorHWPCReportHandler(self.state))
        self.add_handler(PoisonPillMessage, K8sPreProcessorActorPoisonPillMessageHandler(self.state))
