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

from datetime import datetime

import pytest

from powerapi.report import PowerReport


@pytest.fixture
def power_report_without_metadata() -> PowerReport:
    """
    Generates a power_power
    """
    ts = datetime(2020, 1, 1, 0, 0, 0)
    sensor = 'pytest'
    target = 'test'
    power = 42
    metadata = {}
    return PowerReport(ts, sensor, target, power, metadata)


@pytest.fixture
def power_report_with_metadata(power_report_without_metadata) -> PowerReport:
    """
    Generates a power report with single-level metadata.
    """
    power_report_without_metadata.metadata = {
        'scope': 'cpu',
        'socket': 0,
        'formula': '0000000000000000000000000000000000000000'
    }
    return power_report_without_metadata


@pytest.fixture
def power_report_with_metadata_expected_tags(power_report_with_metadata) -> set[str]:
    """
    Returns the expected tags for the power report with single-level metadata.
    """
    return {'sensor', 'target', 'scope', 'socket', 'formula'}


@pytest.fixture
def power_report_with_nested_metadata(power_report_without_metadata) -> PowerReport:
    """
    Generates a power report with nested metadata.
    """
    power_report_without_metadata.metadata = {
        'scope': 'cpu',
        'socket': 0,
        'formula': '0000000000000000000000000000000000000000',
        'k8s': {
            'app.kubernetes.io/name': 'test',
            'app.kubernetes.io/managed-by': 'pytest',
            'helm.sh/chart': 'powerapi-pytest-1.0.0'
        }
    }
    return power_report_without_metadata


@pytest.fixture
def power_report_with_nested_metadata_expected_tags(power_report_with_nested_metadata) -> set[str]:
    """
    Returns the expected tags for the power report with nested metadata.
    """
    return {'sensor', 'target', 'scope', 'socket', 'formula', 'k8s_app_kubernetes_io_name', 'k8s_app_kubernetes_io_managed_by', 'k8s_helm_sh_chart'}
