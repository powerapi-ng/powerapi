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

from powerapi.actor import Actor, State
from powerapi.actor.message import StartMessage, PoisonPillMessage
from powerapi.processor.pre.openstack.handlers import StartMessageHandler, PoisonPillMessageHandler, HWPCReportHandler
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.report import HWPCReport
from .metadata_cache_manager import OpenStackMetadataCacheManager
from .monitor_agent import OpenStackMonitorAgent


class OpenStackProcessorState(State):
    """
    State of the OpenStack processor actor.
    """

    def __init__(self, actor: Actor, polling_interval: float):
        """
        Initializes an OpenStack processor state.
        :param actor: Actor instance
        :param polling_interval: OpenStack API polling interval (in seconds)
        """
        super().__init__(actor)

        self.manager = Manager()
        self.metadata_cache_manager = OpenStackMetadataCacheManager(self.manager)
        self.monitor_agent = OpenStackMonitorAgent(self.metadata_cache_manager, polling_interval)


class OpenStackPreProcessorActor(ProcessorActor):
    """
    Pre-Processor Actor that adds OpenStack related metadata to reports.
    """

    def __init__(self, name: str, polling_interval: float, level_logger: int = logging.WARNING):
        """
        Initializes an OpenStack pre-processor actor.
        :param name: Name of the actor
        :param polling_interval: OpenStack API polling interval (in seconds)
        :param level_logger: Logging level of the actor
        """
        super().__init__(name, level_logger, 5000)

        self.polling_interval = polling_interval

    def setup(self):
        """
        Set up the OpenStack pre-processor actor.
        """
        self.state = OpenStackProcessorState(self, self.polling_interval)

        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(HWPCReport, HWPCReportHandler(self.state))
