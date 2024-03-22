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
from multiprocessing import Manager

from powerapi.actor import Actor
from powerapi.message import StartMessage, PoisonPillMessage
from powerapi.processor.processor_actor import ProcessorState, ProcessorActor
from powerapi.report import HWPCReport
from .handlers import K8sPreProcessorActorHWPCReportHandler
from .handlers import K8sPreProcessorActorStartMessageHandler, K8sPreProcessorActorPoisonPillMessageHandler
from .metadata_cache_manager import K8sMetadataCacheManager
from .monitor_agent import K8sMonitorAgent


class K8sPreProcessorState(ProcessorState):
    """
    State of the Kubernetes pre-processor actor.
    """

    def __init__(self, actor: Actor, target_actors: list, target_actors_names: list, api_mode: str, api_host: str, api_key: str):
        super().__init__(actor, target_actors, target_actors_names)

        self.api_mode = api_mode
        self.api_host = api_host
        self.api_key = api_key

        self.manager = None
        self.metadata_cache_manager = None
        self.monitor_agent = None

    def initialize_metadata_cache_manager(self):
        """
        Initialize the metadata cache manager.
        This method should **ONLY** be called from the pre-processor actor process.
        """
        self.manager = Manager()
        self.metadata_cache_manager = K8sMetadataCacheManager(self.manager)
        self.monitor_agent = K8sMonitorAgent(self.metadata_cache_manager, self.api_mode, self.api_host, self.api_key)


class K8sPreProcessorActor(ProcessorActor):
    """
    Pre-Processor Actor that adds Kubernetes related metadata to reports.
    """

    def __init__(self, name: str, target_actors: list, target_actors_names: list, api_mode: str = None, api_host: str = None,
                 api_key: str = None, level_logger: int = logging.WARNING, timeout: int = 5000):
        super().__init__(name, level_logger, timeout)

        self.state = K8sPreProcessorState(self, target_actors, target_actors_names, api_mode, api_key, api_host)

    def setup(self):
        """
        Set up the Kubernetes pre-processor actor.
        """
        self.state.initialize_metadata_cache_manager()

        self.add_handler(StartMessage, K8sPreProcessorActorStartMessageHandler(self.state))
        self.add_handler(HWPCReport, K8sPreProcessorActorHWPCReportHandler(self.state))
        self.add_handler(PoisonPillMessage, K8sPreProcessorActorPoisonPillMessageHandler(self.state))
