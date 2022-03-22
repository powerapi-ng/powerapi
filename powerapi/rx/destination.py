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

# Author : Daniel Romero Acero
# Last modified : 17 March 2022

##############################
#
# Imports
#
##############################
from abc import abstractmethod

from rx.core.typing import Observer


##############################
#
# Classes
#
##############################


class Destination(Observer):
    """Abstract observer Class for storing reports produced by an observable (e.g., a formula)

    This class defines the required functions provided by a Destination
    """

    def __init__(self) -> None:
        """Creates a new destination as an observer

        Args:

        """
        super().__init__()
        # super().on_next = self.store_report

    @abstractmethod
    def store_report(self, report):
        """Required method for storing a report

        Args:
            report: The report that will be stored
        """
        raise NotImplementedError

    def on_next(self, report) -> None:
        """This method is called when the observer has to process a report

        Args:
            report: The report that will be processed
        """
        self.store_report(report)

    def on_completed(self) -> None:
        """This method is called when the source finished"""
        raise NotImplementedError

    def on_error(self) -> None:
        """This method is called when the source has an error"""
        raise NotImplementedError
