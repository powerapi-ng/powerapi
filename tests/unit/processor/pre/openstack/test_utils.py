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

from powerapi.processor.pre.openstack._utils import get_instance_name_from_libvirt_cgroup


def test_get_instance_name_from_libvirt_cgroup_v1_path():
    """
    Test extracting a libvirt instance name from a cgroup v1 path.
    """
    target = '/machine/machine-qemu-3-instance-00000003.libvirt-qemu'

    assert get_instance_name_from_libvirt_cgroup(target) == 'instance-00000003'


def test_get_instance_name_from_libvirt_cgroup_v2_path():
    """
    Test extracting a libvirt instance name from a cgroup v2 path.
    """
    target = '/machine.slice/machine-qemu-3-instance-00000003.scope/libvirt/emulator'

    assert get_instance_name_from_libvirt_cgroup(target) == 'instance-00000003'


def test_get_instance_name_from_escaped_libvirt_cgroup_v2_path():
    """
    Test extracting a libvirt instance name from an escaped cgroup v2 path.
    """
    target = '/machine.slice/machine-qemu\\x2d3\\x2dinstance\\x2d00000003.scope/libvirt/emulator'

    assert get_instance_name_from_libvirt_cgroup(target) == 'instance-00000003'


def test_get_instance_name_from_non_libvirt_cgroup_path():
    """
    Test extracting a libvirt instance name from a non-libvirt cgroup path.
    """
    assert get_instance_name_from_libvirt_cgroup('/system.slice/system-getty.slice/getty@tty1.service') is None
