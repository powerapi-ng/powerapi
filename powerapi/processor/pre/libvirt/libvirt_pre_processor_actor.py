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
import re

from powerapi.exception import LibvirtException
from powerapi.message import StartMessage
from powerapi.processor.pre.libvirt.libvirt_pre_processor_handlers import LibvirtPreProcessorReportHandler, \
    LibvirtPreProcessorStartHandler
from powerapi.report import Report
from powerapi.actor import Actor
from powerapi.processor.processor_actor import ProcessorActor, ProcessorState

try:
    from libvirt import openReadOnly
except ImportError:
    logging.getLogger().info("libvirt-python is not installed.")

    libvirtError = LibvirtException
    openReadOnly = None


class LibvirtPreProcessorState(ProcessorState):
    """
    State related to a LibvirtPreProcessorActor
    """

    def __init__(self, actor: Actor, uri: str, regexp: str, target_actors: list, target_actors_names: list):
        ProcessorState.__init__(self, actor=actor, target_actors=target_actors, target_actors_names=target_actors_names)
        self.regexp = re.compile(regexp)
        self.daemon_uri = None if uri == '' else uri
        self.libvirt = openReadOnly(self.daemon_uri)


class LibvirtPreProcessorActor(ProcessorActor):
    """
    Processor Actor that modifies reports by replacing libvirt id by open stak uuid
    """

    def __init__(self, name: str, uri: str, regexp: str, target_actors: list = None, target_actors_names: list = None,
                 level_logger: int = logging.WARNING,
                 timeout: int = 5000):
        ProcessorActor.__init__(self, name=name, level_logger=level_logger,
                                timeout=timeout)
        self.state = LibvirtPreProcessorState(actor=self, uri=uri, regexp=regexp, target_actors=target_actors,
                                              target_actors_names=target_actors_names)

    def setup(self):
        """
        Define ReportMessage handler and StartMessage handler
        """
        ProcessorActor.setup(self)
        self.add_handler(message_type=StartMessage, handler=LibvirtPreProcessorStartHandler(state=self.state))
        self.add_handler(message_type=Report, handler=LibvirtPreProcessorReportHandler(state=self.state))
