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

import pytest

from powerapi.utils.metadata import build_metadata_mapping, normalize_metadata_name


@pytest.mark.parametrize(
    ('name', 'prefix', 'expected'),
    [
        ('namespace', 'k8s_label_', 'k8s_label_namespace'),
        ('app.kubernetes.io/name', 'k8s_label_', 'k8s_label_app_kubernetes_io_name'),
        ('application-type/version', 'openstack_metadata_', 'openstack_metadata_application_type_version'),
        ('Consommation Énergie', 'PowerAPI_', 'powerapi_consommation_energie'),
        ('container/name', '', 'container_name'),
        ('test_metadata', 'powerapi_', 'powerapi_test_metadata'),
        ('test_metadata', '', 'test_metadata'),
    ],
)
def test_normalize_metadata_name(name: str, prefix: str, expected: str) -> None:
    """
    Metadata names should be converted to prefixed ASCII identifiers.
    """
    assert normalize_metadata_name(name, prefix) == expected


def test_build_metadata_mapping() -> None:
    """
    Metadata mapping should associate source names with normalized names.
    """
    names = ['app.kubernetes.io/name', 'pytest-example']

    mapping = build_metadata_mapping(names, 'k8s_label_')

    assert mapping == {
        'app.kubernetes.io/name': 'k8s_label_app_kubernetes_io_name',
        'pytest-example': 'k8s_label_pytest_example',
    }


def test_build_metadata_mapping_with_generator() -> None:
    """
    Metadata mapping should accept any iterable of source names.
    """
    names = (name for name in ['application.type', 'environment'])

    mapping = build_metadata_mapping(names, 'openstack_metadata_')

    assert mapping == {
        'application.type': 'openstack_metadata_application_type',
        'environment': 'openstack_metadata_environment',
    }


def test_build_metadata_mapping_ignores_repeated_source_names() -> None:
    """
    Repeated source names should appear only once in the mapping.
    """
    mapping = build_metadata_mapping(['pytest', 'environment', 'pytest'], 'k8s_label_')

    assert list(mapping) == ['pytest', 'environment']
    assert mapping == {
        'pytest': 'k8s_label_pytest',
        'environment': 'k8s_label_environment',
    }


def test_build_metadata_mapping_with_empty_iterable() -> None:
    """
    An empty collection of source names should produce an empty mapping.
    """
    assert build_metadata_mapping([], 'k8s_label_') == {}


def test_build_metadata_mapping_rejects_normalization_collision() -> None:
    """
    Distinct names producing the same normalized name should be rejected.
    """
    a = 'app.kubernetes.io/name'
    b = 'app/kubernetes/io/name'
    normalized = 'test_app_kubernetes_io_name'

    with pytest.raises(ValueError, match=f'Metadata names {a} and {b} both normalize to {normalized}'):
        build_metadata_mapping(['app.kubernetes.io/name', 'app/kubernetes/io/name'], 'test_')
