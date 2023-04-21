# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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

from powerapi.report import FormulaReport


def test_formula_report_to_csv_lines_with_empty_metadata():
    """
    Test if the report without metadata is correctly converted to csv lines.
    """
    ts = datetime.fromtimestamp(0)
    report = FormulaReport(ts, 'pytest', 'formula', {})
    columns, lines = FormulaReport.to_csv_lines(report)

    assert columns == ['timestamp', 'sensor', 'target', 'metadata']
    assert len(lines['FormulaReport']) == 1
    assert lines['FormulaReport'][0]['timestamp'] == int(ts.timestamp() * 1000)  # timestamp in milliseconds
    assert lines['FormulaReport'][0]['sensor'] == 'pytest'
    assert lines['FormulaReport'][0]['target'] == 'formula'
    assert lines['FormulaReport'][0]['metadata'] == '{}'  # metadata is serialized as a string


def test_formula_report_to_csv_lines_with_metadata():
    """
    Test if the report with metadata is correctly converted to csv lines.
    """
    ts = datetime.now()
    report = FormulaReport(ts, 'pytest', 'formula', {'string': 'value', 'int': 1, 'float': 1.0, 'bool': True})
    columns, lines = FormulaReport.to_csv_lines(report)

    assert columns == ['timestamp', 'sensor', 'target', 'metadata']
    assert len(lines['FormulaReport']) == 1
    assert lines['FormulaReport'][0]['timestamp'] == int(ts.timestamp() * 1000)
    assert lines['FormulaReport'][0]['sensor'] == 'pytest'
    assert lines['FormulaReport'][0]['target'] == 'formula'
    assert lines['FormulaReport'][0]['metadata'] == '{"string": "value", "int": 1, "float": 1.0, "bool": true}'


def test_formula_report_to_mongodb_with_empty_metadata():
    """
    Test if the report without metadata is correctly converted to a mongodb document.
    """
    ts = datetime.fromtimestamp(0)
    report = FormulaReport(ts, 'pytest', 'formula', {})
    document = FormulaReport.to_mongodb(report)

    assert document['timestamp'] == ts  # datetime format is supported
    assert document['sensor'] == 'pytest'
    assert document['target'] == 'formula'
    assert document['metadata'] == {}


def test_formula_report_to_mongodb_with_metadata():
    """
    Test if the report with metadata is correctly converted to a mongodb document.
    """
    ts = datetime.now()
    report = FormulaReport(ts, 'pytest', 'formula', {'string': 'value', 'int': 1, 'float': 1.0, 'bool': True})
    document = FormulaReport.to_mongodb(report)

    assert document['timestamp'] == ts
    assert document['sensor'] == 'pytest'
    assert document['target'] == 'formula'
    assert document['metadata'] == {'string': 'value', 'int': 1, 'float': 1.0, 'bool': True}


def test_formula_report_to_influxdb_with_empty_metadata():
    """
    Test if the report without metadata is correctly converted to an influxdb document.
    """
    ts = datetime.fromtimestamp(0)
    report = FormulaReport(ts, 'pytest', 'formula', {})
    document = FormulaReport.to_influxdb(report)

    assert document['measurement'] == 'formula_report'
    assert document['tags'] == {'sensor': 'pytest', 'target': 'formula'}
    assert document['time'] == int(ts.timestamp() * 1000)  # timestamp in milliseconds
    assert document['fields'] == {}


def test_formula_report_to_influxdb_with_metadata():
    """
    Test if the report with metadata is correctly converted to an influxdb document.
    """
    ts = datetime.now()
    report = FormulaReport(ts, 'pytest', 'formula', {'string': 'value', 'int': 1, 'float': 1.0, 'bool': True})
    document = FormulaReport.to_influxdb(report)

    assert document['measurement'] == 'formula_report'
    assert document['tags'] == {'sensor': 'pytest', 'target': 'formula'}
    assert document['time'] == int(ts.timestamp() * 1000)
    assert document['fields'] == {'string': 'value', 'int': 1, 'float': 1.0, 'bool': True}
