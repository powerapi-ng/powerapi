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

from powerapi.actor import State
from powerapi.exception import LibvirtException
from powerapi.processor.handlers import ProcessorReportHandler
from powerapi.handler import StartHandler
from powerapi.report import Report

try:
    from libvirt import libvirtError
except ImportError:
    logging.getLogger().info("libvirt-python is not installed.")

    libvirtError = LibvirtException


class LibvirtPreProcessorReportHandler(ProcessorReportHandler):
    """
    Modify reports by replacing libvirt id by open stak uuid
    """

    def __init__(self, state):
        ProcessorReportHandler.__init__(self, state=state)

    def handle(self, report: Report):
        """
        Modify reports by replacing libvirt id by open stak uuid

        :param Report report: Report to be modified
        """
        result = re.match(self.state.regexp, report.target)
        if result is not None:
            domain_name = result.groups(0)[0]
            try:
                domain = self.state.libvirt.lookupByName(domain_name)
                report.metadata["domain_id"] = domain.UUIDString()
            except libvirtError:
                pass

        self._send_report(report=report)


class LibvirtPreProcessorStartHandler(StartHandler):
    """
    Initialize the target actors
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state=state)

    def initialization(self):
        for actor in self.state.target_actors:
            actor.connect_data()
