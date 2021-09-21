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
import datetime
import logging
import sys
from powerapi.exception import PowerAPIException


class WrongFormatReport(PowerAPIException):
    """
    Exception raised when Sync receive a report which is not of a handled type
    """
    def __init__(self, report_type):
        PowerAPIException.__init__(self)
        self.report_type = report_type


class WrongTypeParameter(PowerAPIException):
    """
    Exception raised when Sync is instantiate with a parameter of the wrong type
    """
    def __init__(self, parameter: str):
        PowerAPIException.__init__(self)
        self.parameter = parameter


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

        if not isinstance(delay, datetime.timedelta):
            raise WrongTypeParameter("delay")

        self.delay = delay
        self.type1 = type1
        self.type2 = type2
        self.type1_buff = []
        self.type2_buff = []
        self.pair_ready = []

    def insert_report(self, report, main_buff, secondary_buff):
        """
        Insert report in the buff and delete obsolete one
        If a pair is found store it it the dedicated buff
        """
        second_report = main_buff[0]
        diff = abs(report.timestamp - second_report.timestamp)

        while diff > self.delay:
            if report.timestamp > second_report.timestamp:
                main_buff.pop(0)

            if report.timestamp < second_report.timestamp:
                return None

            if len(main_buff) == 0:
                secondary_buff.append(report)
                return None

            second_report = main_buff[0]
            diff = abs(report.timestamp - second_report.timestamp)

        if self.type1(report):
            self.pair_ready.append((report, second_report))  # report are in order (type1,type2)
        else:
            self.pair_ready.append((second_report, report))

    def add_report(self, report):
        """
        Receive a new report.
        If there is a report that can be paired with it then it do so
        Else the report is stored in the buffer
        """

        if report in self.type2_buff or report in self.type2_buff:
            logging.error("Duplicate message")
            sys.exit(0)

        if self.type1(report):
            if len(self.type2_buff) == 0:
                self.type1_buff.append(report)
            else:
                self.insert_report(report, self.type2_buff, self.type1_buff)
        elif self.type2(report):
            if len(self.type1_buff) == 0:
                self.type2_buff.append(report)
            else:
                self.insert_report(report, self.type1_buff, self.type2_buff)
        else:
            raise WrongFormatReport(type(report))

    def request(self):
        """
            Request a pair of report
            Return None if there is no pair available
        """
        if len(self.pair_ready) > 0:
            return self.pair_ready.pop(0)
        return None
