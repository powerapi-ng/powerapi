# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

# Author : Daniel  Romero Acero
# Last modified : 17 march 2022

##############################
#
# Imports
#
##############################
from abc import abstractmethod
from typing import Optional

from rx import Observable
from rx.core.typing import Scheduler, Observer, Subject

from powerapi.rx.report import Report
from powerapi.rx.source import Source

##############################
#
# Classes
#
##############################


class Formula(Observable):

    """ Abstract observable and observer Class for retrieving data produced by sensors

    This class defines the required functions provided by a Formula
    """

    def __init__(self) -> None:
        """ Creates a new formula observable

        Args:

        """
        super().__init__()
        self.observers = []

    def __call__(self, source: Source):

        process_report = self.process_report

        def subscribe(operator: Observer, scheduler: Optional[Scheduler] = None):
            """ Required method for subscribing reports computed by the formula

                Args:
                    operator: The observer (e.g. a destination) that will process the output of the formula
                    scheduler: Used for parallelism. Not used for the time being
            """
            nonlocal process_report
            self.observers.append(operator)
            return source.subscribe(
                    process_report,
                    operator.on_error,
                    operator.on_completed,
                    scheduler)

        self._subscribe = subscribe
        return self

    @abstractmethod
    def process_report(self, report:Report):
        """ Required method for processing data as an observer of a source (= on_next method)

                    Args:
                        report: The operator (e.g. a destination) that will process the output of the formula
                """
        raise NotImplementedError



