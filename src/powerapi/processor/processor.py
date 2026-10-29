# Copyright (c) 2026, Inria
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

from collections.abc import Iterable
from typing import Any

from powerapi.report import Report


class ReportProcessor[R: Report]:
    """
    Process reports of a specific type.
    """

    def __init__(self, report_type: type[R]):
        """
        Initialize a report processor for the given report type.
        :param report_type: Report type accepted by the processor
        """
        self.report_type = report_type

    def process(self, report: R) -> R | None:
        """
        Process or drop the incoming report.
        :param report: Report to process
        :return: The report, possibly modified, or None if dropped
        """
        raise NotImplementedError()


class Processor:
    """
    Manage shared resources for report processors.
    """

    def initialize(self) -> None:
        """
        Initialize shared processing resources.
        """

    def get_report_processors(self) -> Iterable[ReportProcessor[Any]]:
        """
        Return initialized report processors for all supported report types.
        :return: Iterable of initialized report processors
        """
        raise NotImplementedError()

    def teardown(self) -> None:
        """
        Clean up resources allocated during initialization.
        """
