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

##############################
#
# Imports
#
##############################

from typing import Optional

from rx import Observable
from rx.core.typing import Scheduler, Observer

##############################
#
# Classes
#
##############################


class BaseSource:

    """ Abstract class that has to be implemented by Data Sources

    This class defines the required functions provided by a data source
    """

    def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
        """ Required method for retrieving data from a source by a Formula

            Args:
                operator: The operator (e.g. a formula or log)  that will process the data
                scheduler: Used for parallelism. Not used for the time being

        """
        raise NotImplementedError

    def close(self):
        """ Closes the access to the data source"""
        raise NotImplementedError

    def __del__(self):
        """ When object deleted, connection to data source has to be close"""
        self.close()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """ When application ends, connection to data source has to be close"""
        self.close()


class Source(Observable):

    """ Observable Class for retrieving data produced by sensors

    This class enable via le method subscribe the retrieving of data produced by a sensor
    """

    def __init__(self, base_source: BaseSource) -> None:

        """ Creates a new data source observable by using the given source
        
        Args:
            base_source: Base source for creating an observer source
        """

        super().__init__(base_source.subscribe)

##############################
#
# Functions
#
##############################


def source(base_source: BaseSource) -> Source:
    """Returns an observable source

    Args:
        base_source: Base source for creating an observer source

    """
    return Source(base_source)

