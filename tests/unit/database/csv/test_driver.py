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
from pathlib import Path

import pytest

from powerapi.database.csv.driver import CSVInput, CSVInputFactory, CSVOutput, CSVOutputFactory
from powerapi.report import FormulaReport, HWPCReport, PowerReport, Report


@pytest.mark.parametrize('report_type', [HWPCReport])
def test_create_csv_input(report_type: type[Report]) -> None:
    """
    Factory should create a CSV input for supported report types.
    """
    factory = CSVInputFactory(report_type, ['core.csv', 'msr.csv'])

    csv_input = factory.create()

    assert isinstance(csv_input, CSVInput)
    assert csv_input.input_filepaths == [Path('core.csv'), Path('msr.csv')]


@pytest.mark.parametrize('report_type', [Report, PowerReport, FormulaReport])
def test_create_csv_input_factory_with_unsupported_report_type(report_type: type[Report]) -> None:
    """
    Factory should reject report types unsupported by the CSV input.
    """
    with pytest.raises(ValueError, match=f'Unsupported report type: {report_type.__name__}'):
        CSVInputFactory(report_type, ['core.csv'])


def test_csv_input_factory_is_picklable() -> None:
    """
    Factory arguments should be picklable so it can be passed to an actor running in a separate process.
    """
    factory = CSVInputFactory(HWPCReport, ['core.csv', 'msr.csv'])

    pickle.dumps(factory)


@pytest.mark.parametrize('report_type', [PowerReport, FormulaReport])
def test_create_csv_output(report_type: type[Report]) -> None:
    """
    Factory should create a CSV output for supported report types.
    """
    factory = CSVOutputFactory(report_type, 'output')

    csv_output = factory.create()

    assert isinstance(csv_output, CSVOutput)
    assert csv_output.output_directory == Path('output')


@pytest.mark.parametrize('report_type', [Report, HWPCReport])
def test_create_csv_output_factory_with_unsupported_report_type(report_type: type[Report]) -> None:
    """
    Factory should reject report types unsupported by the CSV output.
    """
    with pytest.raises(ValueError, match=f'Unsupported report type: {report_type.__name__}'):
        CSVOutputFactory(report_type, 'output')


def test_csv_output_factory_is_picklable() -> None:
    """
    Factory arguments should be picklable so it can be passed to an actor running in a separate process.
    """
    factory = CSVOutputFactory(PowerReport, 'output')

    pickle.dumps(factory)
