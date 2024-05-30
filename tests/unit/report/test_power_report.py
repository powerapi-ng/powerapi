# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

from powerapi.report import PowerReport, BadInputData
from datetime import datetime

from tests.utils.report.power import gen_json_power_report


def get_expected_metadata_power_report_without_tag_list(report: PowerReport) -> dict:
    """
    Generates the expected metadata dict for the report with the gen_tag function
    :param report The report to extract the metadata
    """
    metadata = report.metadata
    metadata['sensor'] = report.sensor
    metadata['target'] = report.target

    return metadata


def get_expected_metadata_power_report_with_tags(report: PowerReport, tags: list) -> dict:
    """
    Generates the expected metadata dict for the report with the gen_tag function
    :param report: The report to extract the metadata
    :param tags: The tags to be kept
    """
    metadata = {'sensor': report.sensor, 'target': report.target}

    for tag in tags:
        metadata[tag] = report.metadata[tag]

    return metadata


def get_expected_influxdb_document(report: PowerReport, tags: list) -> dict:
    """
    Generates a dictionary that represents the expected influxdb document for a given dictionary
    :param report: The report for generating the document
    :param tags: The tags to be kept
    """
    return {
        'measurement': 'power_consumption',
        'tags': get_expected_metadata_power_report_with_tags(report, tags) if tags else
        get_expected_metadata_power_report_without_tag_list(report),
        'time': str(report.timestamp),
        'fields': {
            'power': report.power
        }
    }


def get_expected_prometheus_document(report: PowerReport, tags: list) -> dict:
    """
    Generates a dictionary that represents the expected prometheus document for a given dictionary
    :param report: The report for generating the document
    :param tags: The tags to be kept
    """
    return {
        'tags': get_expected_metadata_power_report_with_tags(report, tags) if tags else
        get_expected_metadata_power_report_without_tag_list(report),
        'time': int(report.timestamp.timestamp()),
        'value': report.power
    }


def check_report_metadata(original_metadata: dict, report: PowerReport):
    """
    Check that the metadata of a report didn't change
    :param original_metadata: Orignal's report metadata
    :param report: Report for checking metadata
    """
    assert report.metadata == original_metadata


########
# JSON #
########
def test_create_power_report_from_json_wit_str_timestamp_create_a_PowerReport():
    json_input = gen_json_power_report(1)[0]
    report = PowerReport.from_json(json_input)
    assert isinstance(report, PowerReport)


def test_create_power_report_from_json_with_datetime_timestamp_format_create_a_PowerReport():
    json_input = gen_json_power_report(1)[0]
    json_input['timestamp'] = datetime.strptime(json_input['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
    report = PowerReport.from_json(json_input)
    assert isinstance(report, PowerReport)


def test_create_power_report_from_json_with_str_timestamp_with_bad_format_raise_BadInputData():
    json_input = gen_json_power_report(1)[0]
    json_input['timestamp'] = '1970-09-01T090909.543'
    with pytest.raises(BadInputData):
        _ = PowerReport.from_json(json_input)


def test_create_power_report_from_json_without_timestamp_field_raise_BadInputData():
    json_input = gen_json_power_report(1)[0]
    del json_input['timestamp']
    with pytest.raises(BadInputData):
        _ = PowerReport.from_json(json_input)


def test_create_power_report_from_json_without_sensor_field_raise_BadInputData():
    json_input = gen_json_power_report(1)[0]
    del json_input['sensor']
    with pytest.raises(BadInputData):
        _ = PowerReport.from_json(json_input)


#######
# CSV #
#######
def test_create_power_report_from_csv_with_one_lines_create_an_power_report():
    csv_lines = [("power",
                  {
                      "timestamp": "2021-09-14T12:37:37.168817",
                      "sensor": "formula_group",
                      "target": "all",
                      "power": 42
                  }
                  )
                 ]
    report = PowerReport.from_csv_lines(csv_lines)
    assert isinstance(report, PowerReport)


def test_create_power_report_from_csv_with_bad_timestamp_format_raise_BadInputData():
    csv_lines = [("power",
                  {
                      "timestamp": '1970-09-01T090909.543',
                      "sensor": "formula_group",
                      "target": "all",
                      "power": 42
                  }
                  )
                 ]
    with pytest.raises(BadInputData):
        _ = PowerReport.from_csv_lines(csv_lines)


def test_create_power_report_from_csv_with_two_lines_raise_BadInputData():
    csv_lines = [("power",
                  {
                      "timestamp": "2021-09-14T12:37:37.168817",
                      "sensor": "formula_group",
                      "target": "all",
                      "power": 42
                  }
                  ),
                 ("power",
                  {
                      "timestamp": "2021-09-14T12:37:37.168817",
                      "sensor": "formula_group",
                      "target": "all",
                      "power": 42
                  }
                  )
                 ]
    with pytest.raises(BadInputData):
        _ = PowerReport.from_csv_lines(csv_lines)


############
# METADATA #
############

def test_creating_report_with_metadata():
    report = PowerReport(('1970-09-01T09:09:10.543'), 'toto', 'all', 42, {"tag": 1})
    assert report.metadata["tag"] == 1


def test_create_report_from_json_with_metadata():
    json_input = gen_json_power_report(1)[0]
    json_input["metadata"] = {}
    json_input["metadata"]["tag"] = 1
    report = PowerReport.from_json(json_input)
    assert report.metadata["tag"] == 1


def test_create_report_from_csv_with_metadata():
    csv_lines = [("power",
                  {
                      "timestamp": "2021-09-14T12:37:37.168817",
                      "sensor": "formula_group",
                      "target": "all",
                      "power": 42,
                      "tag": 1
                  }
                  )
                 ]
    report = PowerReport.from_csv_lines(csv_lines)
    assert report.metadata["tag"] == 1


def test_gen_tag_keep_all_the_report_metadata_without_tags_list_and_empty_metadata(power_report_without_metadata):
    tags = []
    original_metadata = power_report_without_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_without_metadata)

    metadata = power_report_without_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_without_metadata)


def test_gen_tag_keep_all_the_report_metadata_without_tag_list_and_empty_metadata(power_report_without_metadata):
    tags = None
    original_metadata = power_report_without_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_without_metadata)

    metadata = power_report_without_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_without_metadata)


def test_gen_tag_keep_all_the_report_metadata_with_empty_tag_list(power_report_with_metadata):
    tags = []
    original_metadata = power_report_with_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_with_metadata)

    metadata = power_report_with_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_metadata)


def test_gen_tag_keep_all_the_report_metadata_without_tags(power_report_with_metadata):
    tags = None
    original_metadata = power_report_with_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_with_metadata)

    metadata = power_report_with_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_metadata)


def test_gen_tag_keep_all_the_report_nested_metadata_with_empty_tag_list(power_report_with_nested_metadata):
    tags = []
    original_metadata = power_report_with_nested_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_with_nested_metadata)

    metadata = power_report_with_nested_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_nested_metadata)


def test_gen_tag_keep_all_the_report_nested_metadata_without_tags(power_report_with_nested_metadata):
    tags = None
    original_metadata = power_report_with_nested_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_without_tag_list(power_report_with_nested_metadata)

    metadata = power_report_with_nested_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_nested_metadata)


def test_gen_tag_keep_all_the_report_metadata_with_all_tags(power_report_with_metadata):
    tags = ['k1', 'k2', 'k3', 'k4']
    original_metadata = power_report_with_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_with_tags(power_report_with_metadata, tags)

    metadata = power_report_with_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_metadata)


def test_gen_tag_keep_some_report_metadata_with_some_tags(power_report_with_metadata):
    tags = ['k1', 'k4']
    original_metadata = power_report_with_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_with_tags(power_report_with_metadata, tags)

    metadata = power_report_with_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_metadata)


def test_gen_tag_keep_all_the_report_nested_metadata_with_all_tags(power_report_with_nested_metadata):
    tags = ['k1', 'k2', 'k3', 'k4']
    original_metadata = power_report_with_nested_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_with_tags(power_report_with_nested_metadata, tags)

    metadata = power_report_with_nested_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_nested_metadata)


def test_gen_tag_keep_some_report_nested_metadata_with_some_tags(power_report_with_nested_metadata):
    tags = ['k1', 'k4']
    original_metadata = power_report_with_nested_metadata.metadata
    expected_metadata = get_expected_metadata_power_report_with_tags(power_report_with_nested_metadata, tags)

    metadata = power_report_with_nested_metadata.gen_tag(tags)

    assert metadata == expected_metadata
    check_report_metadata(original_metadata, power_report_with_nested_metadata)


def test_gen_tag_raise_exception_with_wrong_tags(power_report_with_metadata):
    tags = ['kx', 'k4']
    original_metadata = power_report_with_metadata.metadata

    with pytest.raises(BadInputData):
        _ = power_report_with_metadata.gen_tag(tags)

    check_report_metadata(original_metadata, power_report_with_metadata)


def test_gen_tag_raise_exception_with_wrong_tags_and_nested_metadata(power_report_with_nested_metadata):
    tags = ['k1', 'k4_k2_k1']
    original_metadata = power_report_with_nested_metadata.metadata

    with pytest.raises(BadInputData):
        _ = power_report_with_nested_metadata.gen_tag(tags)

    check_report_metadata(original_metadata, power_report_with_nested_metadata)


def test_to_influxdb_doesnt_add_extra_metadata_for_power_report_with_empty_metadata_and_empty_tag_list(
        power_report_without_metadata):
    tags = []
    expected_influxdb_document = get_expected_influxdb_document(power_report_without_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_without_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_doesnt_add_extra_metadata_for_power_report_with_empty_metadata_and_without_tags(
        power_report_without_metadata):
    tags = None
    expected_influxdb_document = get_expected_influxdb_document(power_report_without_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_without_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_all_metadata_for_power_report_with_metadata_and_empty_tag_list(
        power_report_with_metadata):
    tags = []
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_all_metadata_for_power_report_with_metadata_and_without_tags(
        power_report_with_metadata):
    tags = None
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_all_metadata_for_power_report_with_metadata_and_all_tags(
        power_report_with_metadata):
    tags = ['k1', 'k2', 'k3', 'k4']
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_all_metadata_for_power_report_with_nested_metadata_and_all_tags(
        power_report_with_nested_metadata):
    tags = ['k1', 'k2', 'k3', 'k4']
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_nested_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_nested_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_some_metadata_for_power_report_with_metadata_and_some_tags(
        power_report_with_metadata):
    tags = ['k1', 'k2', 'k4']
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_add_some_metadata_for_power_report_with_nested_metadata_and_some_tags(
        power_report_with_nested_metadata):
    tags = ['k1', 'k3', 'k4']
    expected_influxdb_document = get_expected_influxdb_document(power_report_with_nested_metadata, tags)

    influxdb_document = PowerReport.to_influxdb(power_report_with_nested_metadata, tags)

    assert influxdb_document == expected_influxdb_document


def test_to_influxdb_raise_exception_for_power_report_with_metadata_and_some_tags(
        power_report_with_metadata):
    tags = ['k8888', 'k2', 'k4']

    with pytest.raises(BadInputData):
        _ = PowerReport.to_influxdb(power_report_with_metadata, tags)


def test_to_influxdb_raise_exception_with_wrong_tags_and_nested_metadata(
        power_report_with_nested_metadata):
    tags = ['k1', 'k4_k1', 'k333']

    with pytest.raises(BadInputData):
        _ = PowerReport.to_influxdb(power_report_with_nested_metadata, tags)


def test_to_prometheus_doesnt_add_extra_metadata_for_power_report_with_empty_metadata_and_empty_tag_list(
        power_report_without_metadata):
    tags = []
    expected_prometheus_document = get_expected_prometheus_document(power_report_without_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_without_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_doesnt_add_extra_metadata_for_power_report_with_empty_metadata_and_without_tags(
        power_report_without_metadata):
    tags = None
    expected_prometheus_document = get_expected_prometheus_document(power_report_without_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_without_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_all_metadata_for_power_report_with_metadata_and_empty_tag_list(
        power_report_with_metadata):
    tags = []
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_all_metadata_for_power_report_with_metadata_and_without_tags(
        power_report_with_metadata):
    tags = None
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_all_metadata_for_power_report_with_metadata_and_all_tags(
        power_report_with_metadata):
    tags = ['k2', 'k3', 'k1', 'k4']
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_all_metadata_for_power_report_with_nested_metadata_and_all_tags(
        power_report_with_nested_metadata):
    tags = ['k1', 'k2', 'k3', 'k4']
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_nested_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_nested_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_some_metadata_for_power_report_with_metadata_and_some_tags(
        power_report_with_metadata):
    tags = ['k4', 'k3', 'k1']
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_add_some_metadata_for_power_report_with_nested_metadata_and_some_tags(
        power_report_with_nested_metadata):
    tags = ['k1', 'k2', 'k4']
    expected_prometheus_document = get_expected_prometheus_document(power_report_with_nested_metadata, tags)

    prometheus_document = PowerReport.to_prometheus(power_report_with_nested_metadata, tags)

    assert prometheus_document == expected_prometheus_document


def test_to_prometheus_raise_exception_for_power_report_with_metadata_and_some_tags(
        power_report_with_metadata):
    tags = ['k888', 'k2', 'k4']

    with pytest.raises(BadInputData):
        _ = PowerReport.to_prometheus(power_report_with_metadata, tags)


def test_to_prometheus_raise_exception_with_wrong_tags_and_nested_metadata(
        power_report_with_nested_metadata):
    tags = ['k1', 'k4_k1', 'k333']

    with pytest.raises(BadInputData):
        _ = PowerReport.to_prometheus(power_report_with_nested_metadata, tags)
