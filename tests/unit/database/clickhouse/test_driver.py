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

import pickle

import pytest

pytest.importorskip('powerapi.database.clickhouse.driver')  # The ClickHouse driver requires external dependencies to work.

from powerapi.database.clickhouse.driver import ClickHouseOutput, ClickHouseOutputFactory
from powerapi.report import PowerReport, Report, HWPCReport, FormulaReport


@pytest.mark.parametrize('report_type', [PowerReport])
def test_create_clickhouse_output(report_type: type[Report]) -> None:
    """
    Factory should create a ClickHouse output for supported report types.
    """
    factory = ClickHouseOutputFactory(report_type, 'localhost', 8123, 'pytest', 'pytest', 'powerapi')

    output = factory.create()

    assert isinstance(output, ClickHouseOutput)
    assert output.host == 'localhost'
    assert output.port == 8123
    assert output.username == 'pytest'
    assert output.password == 'pytest'
    assert output.database_name == 'powerapi'


@pytest.mark.parametrize('report_type', [Report, HWPCReport, FormulaReport])
def test_create_factory_with_unsupported_report_type(report_type: type[Report]) -> None:
    """
    Factory should reject report types unsupported by the ClickHouse output.
    """
    with pytest.raises(ValueError, match=f'Unsupported report type: {report_type.__name__}'):
        ClickHouseOutputFactory(report_type, 'localhost', 8123, 'pytest', 'pytest', 'powerapi')


def test_clickhouse_output_factory_is_picklable() -> None:
    """
    Factory arguments should be picklable so it can be passed to an actor running in a separate process.
    """
    factory = ClickHouseOutputFactory(PowerReport, 'localhost', 8123, 'pytest', 'pytest', 'powerapi')

    pickle.dumps(factory)
