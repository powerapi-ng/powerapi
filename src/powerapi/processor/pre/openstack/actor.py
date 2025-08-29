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

from powerapi.actor import Actor
from powerapi.message import StartMessage, PoisonPillMessage
from powerapi.processor.pre.openstack.handlers import StartMessageHandler, PoisonPillMessageHandler, HWPCReportHandler
from powerapi.processor.processor_actor import ProcessorState, ProcessorActor
from powerapi.report import HWPCReport
from .metadata_cache_manager import OpenStackMetadataCacheManager


class OpenStackPreProcessorState(ProcessorState):
    """
    State of the OpenStack pre-processor actor.
    """

    def __init__(self, actor: Actor, target_actors: list, target_actors_names: list):
        """
        :param actor: Actor instance
        :param target_actors: list of target actors
        :param target_actors_names: list of target actor names
        """
        super().__init__(actor, target_actors, target_actors_names)

        self.metadata_cache_manager = OpenStackMetadataCacheManager()


class OpenStackPreProcessorActor(ProcessorActor):
    """
    Pre-Processor Actor that adds OpenStack related metadata to reports.
    """

    def __init__(self, name: str, target_actors: list, target_actors_names: list, level_logger: int = logging.WARNING):
        """
        :param name: Name of the actor
        :param target_actors: List of target actors
        :param target_actors_names: List of target actor names
        :param level_logger: Logging level of the actor
        """
        super().__init__(name, level_logger, 5000)

        self.state = OpenStackPreProcessorState(self, target_actors, target_actors_names)

    def setup(self):
        """
        Set up the OpenStack pre-processor actor.
        """
        self.add_handler(StartMessage, StartMessageHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))

        self.add_handler(HWPCReport, HWPCReportHandler(self.state))
