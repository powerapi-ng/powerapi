# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

from queue import Queue
import datetime
from powerapi.exception import PowerAPIException


class WrongFormatReport(PowerAPIException):
    """
    Exception raised when Sync receive a report which is not of a handled type
    """
    def __init__(self, report_type):
        PowerAPIException.__init__(self)
        self.report_type = report_type


class Sync():
    """
    Sync class

    Class that receive asynchronous data and synchronize them using their timestamp
    """
    def __init__(self, type1, type2, delay):
        """
        type1 : Report -> bool.
        Function that return true if the report can be identified as the first type of report

        type2 : Report -> bool.
        Function that return true if the report can be identified as the second type of report

        delay : float
        maximal delay, in second, that is allowed between two report to pair them
        """

        self.delay = delay
        self.type1 = type1
        self.type2 = type2
        self.type1_buff = Queue()
        self.type2_buff = Queue()
        self.pair_ready = Queue()

    def add_report(self, report):
        """
        Receive a new report.
        If there is a report that can be paired with it then it do so
        Else the report is stored in the buffer
        """
        if self.type1(report):
            if self.type2_buff.qsize() == 0:
                self.type1_buff.put(report)
            else:
                second_report = self.type2_buff.get()
                diff = abs(report.timestamp - second_report.timestamp)

                while diff > self.delay:
                    if self.type2_buff.qsize() == 0:
                        self.type1_buff.put(report)
                        return None

                    second_report = self.type2_buff.get()
                    diff = abs(report.timestamp - second_report.timestamp)

                self.pair_ready.put((report, second_report))  # report are in order (type1,type2)

        elif self.type2(report):
            if self.type1_buff.qsize() == 0:
                self.type2_buff.put(report)
            else:
                second_report = self.type1_buff.get()
                diff = abs(report.timestamp - second_report.timestamp)

                while diff > self.delay:
                    if self.type1_buff.qsize() == 0:
                        self.type2_buff.put(report)
                        return None

                    second_report = self.type1_buff.get()
                    diff = abs(report.timestamp - second_report.timestamp)

                self.pair_ready.put((second_report, report))  # report are in order (type1,type2)

        else:
            raise WrongFormatReport(type(report))
        return None

    def request(self):
        """
            Request a pair of report
            Return None if there is no pair available
        """
        if self.pair_ready.qsize() > 0:
            return self.pair_ready.get()
        return None
