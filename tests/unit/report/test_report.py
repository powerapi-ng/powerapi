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

from datetime import datetime

from powerapi.report import Report


def test_creating_report_with_metadata():
    """
    Test creating a report with metadata.
    """
    report = Report(datetime.now(), 'pytest', 'test', {'tag1': 1, 'tag2': {'2'}, 'tag3': '3'})

    assert report.metadata["tag1"] == 1
    assert report.metadata["tag2"] == {'2'}
    assert report.metadata["tag3"] == '3'


def test_create_two_report_without_metadata_metadata_are_different():
    """
    When using a default parameter, its value is evaluated at the instantiation of the class
    So if not used carefully, all object have the same value as attribute
    """

    a = Report(0, 'toto', 'all')
    a.metadata["test"] = "value"
    b = Report(0, 'toto', 'all')
    assert a.metadata != b.metadata


def test_sanitize_tags_name():
    """
    Test sanitizing tag names from the metadata dictionary.
    """
    tags = ['test-tag', 'app.kubernetes.io/name', 'helm.sh/chart']
    sanitized_tags = Report.sanitize_tags_name(tags)

    assert len(sanitized_tags) == len(tags)
    assert sanitized_tags['test-tag'] == 'test_tag'
    assert sanitized_tags['app.kubernetes.io/name'] == 'app_kubernetes_io_name'
    assert sanitized_tags['helm.sh/chart'] == 'helm_sh_chart'


def test_flatten_metadata_dict():
    """
    Test flattening a report metadata dictionary.
    """
    report_metadata = {
        'scope': 'cpu',
        'socket': 0,
        'formula': '13edcdfbd3743bec4002a092cb39fbff20a175eb',
        'k8s': {
            'app.kubernetes.io/name': 'test-flatten',
            'app.kubernetes.io/instance': 'test-abcxyz',
            'app.kubernetes.io/managed-by': 'pytest',
            'helm.sh/chart': 'powerapi-pytest-1.0.0'
        }
    }
    flattened_metadata = Report.flatten_tags(report_metadata, '/')

    assert flattened_metadata['scope'] == 'cpu'
    assert flattened_metadata['socket'] == 0
    assert flattened_metadata['formula'] == '13edcdfbd3743bec4002a092cb39fbff20a175eb'
    assert flattened_metadata['k8s/app.kubernetes.io/name'] == 'test-flatten'
    assert flattened_metadata['k8s/app.kubernetes.io/instance'] == 'test-abcxyz'
    assert flattened_metadata['k8s/app.kubernetes.io/managed-by'] == 'pytest'
    assert flattened_metadata['k8s/helm.sh/chart'] == 'powerapi-pytest-1.0.0'
