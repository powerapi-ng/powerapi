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

from rx.core.typing import Observer, Scheduler
from typing import Optional, Dict, Any
from datetime import datetime

from powerapi.rx.formula import Formula
from powerapi.rx.report import Report, TARGET_CN
from powerapi.rx.reports_group import ReportsGroup, TIMESTAMP_CN, SENSOR_CN, METADATA_CN
from powerapi.rx.source import BaseSource, source
from powerapi.rx.destination import Destination

##############################
#
# Constants
#
##############################
GROUPS_CN = "groups"
SUB_GROUPS_L1_CN = "sub_group_l1"
SUB_GROUPS_L2_CN = "sub_group_l2"


##############################
#
# Classes
#
##############################


class SimpleFormula(Formula):
    """Simple formula for testing the usage of the framework"""

    def __init__(self) -> None:
        """ Creates a fake formula

        Args:

        """
        super().__init__()

    def process_report(self, reports: ReportsGroup):
        """ Required method for processing data as an observer of a source

                    Args:
                        report: The operator (e.g. a destination) that will process the output of the formula
                """

        reports.processed = True

        for observer in self.observers:
            observer.on_next(reports)


class ComplexFormula(Formula):
    """Complex formula for testing the usage of the framework"""

    def __init__(self) -> None:
        """ Creates a fake formula

        Args:

        """
        super().__init__()

    def process_report(self, reports: ReportsGroup):
        """ Required method for processing data as an observer of a source

            Args:
            report: The operator (e.g. a destination) that will process the output of the formula
        """

        report_dict = {
            "timestamp": "2022-02-21T14:53:50.152Z",
            "sensor": "sensor",
            "target": "cool_noyce",
            "metadata": {
                "scope": "cpu",
                "socket": "0",
                "formula": "624236cabf67b95a8dd714529b91c19f162ab94d",
                "ratio": 1,
                "predict": 164.9913654183235,
                "power_units": "watt"},
            "power": 164.9913654183235}

        new_reports = ReportsGroup.create_reports_group_from_dicts([report_dict])

        for observer in self.observers:
            observer.on_next(new_reports)


class SimpleSource(BaseSource):
    """Simple source for testing purposes"""

    def __init__(self, reports: ReportsGroup) -> None:
        """ Creates a fake source

        Args:

        """
        super().__init__()
        self.reports = reports

    def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
        """ Required method for retrieving data from a source by a Formula

            Args:
                operator: The operator (e.g. a formula or log)  that will process the data
                scheduler: Used for parallelism. Not used for the time being

        """
        operator.on_next(self.reports)

    def close(self):
        """ Closes the access to the data source"""
        pass


class SimpleDestination(Destination):
    """Simple destination for testing purposes"""

    def __init__(self) -> None:
        """ Creates a fake source

        Args:

        """
        super().__init__()
        self.reports = None

    def store_report(self, reports):
        """ Required method for storing a report

            Args:
                reports: The report group that will be stored
        """
        self.reports = reports

    def on_completed(self) -> None:
        pass

    def on_error(self, error: Exception) -> None:
        pass

##############################
#
# Tests
#
##############################


def test_simple_formula():
    """ This test only check if different method on source, destination and formula are called"""
    # Setup

    formula = SimpleFormula()

    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target"}

    reports = ReportsGroup.create_reports_group_from_dicts([report_dict])
    reports.is_test = True
    reports.processed = False

    the_source = SimpleSource(reports)
    destination = SimpleDestination()

    # Exercise
    source(the_source).pipe(formula).subscribe(destination)
    # Check Report has been modified
    assert destination.reports is not None
    assert destination.reports.is_test
    assert destination.reports.processed


def test_complex_formula():
    """ Check that on_next method is called on a formula """
    # Setup

    formula = ComplexFormula()
    destination = SimpleDestination()

    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"},
        "groups": {"core":
            {0:
                {0:
                    {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428}}}}}

    the_source = SimpleSource(ReportsGroup.create_reports_group_from_dicts([report_dict]))

    # Exercise
    source(the_source).pipe(formula).subscribe(destination)
    # Check that a new report has been created, i.e., all source, formula and destination have been called
    assert "power" in destination.reports.report.columns  # The produced report has a column power
