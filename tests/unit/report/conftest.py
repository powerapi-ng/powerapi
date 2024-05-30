# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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
import pytest

from powerapi.report import PowerReport
from tests.utils.report.power import gen_json_power_report


@pytest.fixture
def power_report_without_metadata() -> PowerReport:
    """
    Generates a power_power
    """
    json_input = gen_json_power_report(1)[0]
    report = PowerReport.from_json(json_input)

    return report


@pytest.fixture
def power_report_with_metadata(power_report_without_metadata) -> PowerReport:
    """
    Generates a power_power
    """
    power_report_without_metadata.metadata = {'k1': 'v1',
                                              'k2': 'v2',
                                              'k3': 333,
                                              'k4': 'vv4'}

    return power_report_without_metadata


@pytest.fixture
def power_report_with_nested_metadata(power_report_without_metadata) -> PowerReport:
    """
    Generates a power_power
    """
    power_report_without_metadata.metadata = {'k1': {'k1_k1': 1},
                                              'k2': 'v2',
                                              'k3': 333,
                                              'k4': {'k4_k1': 'v1',
                                                     'k4_k2': {'k4_k2_k1': 'v2'}
                                                     }
                                              }

    return power_report_without_metadata
