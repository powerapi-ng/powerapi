# Copyright (c) 2023, Inria
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

import os

from powerapi.processor.pre.k8s._utils import extract_container_id_from_k8s_cgroups_path
from powerapi.processor.pre.k8s._utils import is_target_a_valid_k8s_cgroups_path


def test_extract_docker_container_id_from_cgroups_v2_path():
    """
    Test the container id extraction from a Kubernetes cgroups v2 path using docker.
    """
    path = os.path.join(
        '/kubepods.slice',
        'kubepods-burstable.slice',  # QoS
        'kubepods-burstable-pod435532e3_546d_45e2_8862_d3c7b320d2d9.slice',  # POD
        'docker-68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a.scope'  # Container
    )

    expected_container_id = '68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a'
    assert extract_container_id_from_k8s_cgroups_path(path) == expected_container_id


def test_extract_containerd_container_id_from_cgroups_v2_path():
    """
    Test the container id extraction from a Kubernetes cgroups v2 path using containerd cri.
    """
    path = os.path.join(
        '/kubepods.slice',
        'kubepods-burstable.slice',  # QoS
        'kubepods-burstable-pod2fc932ce_fdcc_454b_97bd_aadfdeb4c340.slice',  # POD
        'cri-containerd-aaefb9d8feed2d453b543f6d928cede7a4dbefa6a0ae7c9b990dd234c56e93b9.scope'  # Container
    )

    expected_container_id = 'aaefb9d8feed2d453b543f6d928cede7a4dbefa6a0ae7c9b990dd234c56e93b9'
    assert extract_container_id_from_k8s_cgroups_path(path) == expected_container_id


def test_extract_crio_container_id_from_cgroups_v2_path():
    """
    Test the container id extraction from a Kubernetes cgroups v2 path using cri-o cri.
    """
    path = os.path.join(
        '/kubepods.slice',
        'kubepods-besteffort.slice',  # QoS
        'kubepods-besteffort-podad412dfe_3589_4056_965a_592356172968.slice',  # POD
        'crio-77b019312fd9825828b70214b2c94da69c30621af2a7ee06f8beace4bc9439e5.scope'  # Container
    )

    expected_container_id = '77b019312fd9825828b70214b2c94da69c30621af2a7ee06f8beace4bc9439e5'
    assert extract_container_id_from_k8s_cgroups_path(path) == expected_container_id


def test_extract_docker_container_id_from_cgroups_v1_path():
    """
    Test the container id extraction from a Kubernetes cgroups v1 path.
    """
    path = os.path.join(
        '/kubepods',
        'besteffort',  # QoS
        'pod42006d2c-cad7-4575-bfa3-91848a558743',  # POD
        'ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5'  # Container
    )

    expected_container_id = 'ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5'
    assert extract_container_id_from_k8s_cgroups_path(path) == expected_container_id


def test_check_k8s_cgroups_path_with_target_name():
    """
    Test check of Kubernetes cgroups path with a target name (not a path)
    """

    assert is_target_a_valid_k8s_cgroups_path('test-container-name') is False

    # Commonly used as placeholder by hwpc-sensor:
    assert is_target_a_valid_k8s_cgroups_path('all') is False
    assert is_target_a_valid_k8s_cgroups_path('global') is False
    assert is_target_a_valid_k8s_cgroups_path('kernel') is False


def test_check_k8s_cgroups_path_with_docker_path():
    """
    Test check of Kubernetes cgroups path with a Docker path.
    """
    path = os.path.join(
        '/docker',
        '2e5acbd1ebe1e41beec860d5de2b6054d33ea4e3ccf7554b02ace778fad22888'
    )

    assert is_target_a_valid_k8s_cgroups_path(path) is False


def test_check_k8s_cgroups_path_with_podman_path():
    """
    Test check of Kubernetes cgroups path with a Podman path.
    """
    path = os.path.join(
        '/user.slice'
        'user-1000.slice',
        'user@1000.service',
        'user.slice',
        'libpod-3256dae0d186e5fa8713d9306699023dfa9723398504ba36eee776295408530d.scope'
    )

    assert is_target_a_valid_k8s_cgroups_path(path) is False
