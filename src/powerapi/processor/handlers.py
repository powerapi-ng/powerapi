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

from powerapi.actor import InitializedStateHandler, State
from powerapi.processor.processor import ReportProcessor
from powerapi.report import Report


class ProcessorReportHandler[ReportT: Report](InitializedStateHandler[ReportT]):
    """
    Process incoming reports and forward retained results.
    """

    def __init__(self, state: State, processor: ReportProcessor[ReportT]):
        """
        Initialize a report handler with its processing implementation.
        :param state: Actor state used for initialization gating and forwarding
        :param processor: Processor accepting the registered report type
        """
        super().__init__(state)
        self._report_processor = processor

    def handle(self, msg: ReportT) -> None:
        """
        Process a report and forward it unless it was dropped.
        :param msg: Incoming report
        """
        report = self._report_processor.process(msg)
        if report is not None:
            self._send_report(report)

    def _send_report(self, report: Report) -> None:
        """
        Send the processed report to all target actors.
        :param report: Report to send
        """
        for target in self.state.actor.target_actors:
            target.send_data(report)
