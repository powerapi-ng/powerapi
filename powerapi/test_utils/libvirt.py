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
try:
    from libvirt import libvirtError
except ImportError:
    from powerapi.report_modifier.libvirt_mapper import LibvirtException
    libvirtError = LibvirtException

DOMAIN_NAME_1 = 'instance-00000001'
DOMAIN_NAME_2 = 'instance-00000999'

LIBVIRT_TARGET_NAME1 = '/machine/qemu-1-' + DOMAIN_NAME_1 + '.libvirt-qemu'
LIBVIRT_TARGET_NAME2 = '/machine/qemu-2-' + DOMAIN_NAME_2 + '.libvirt-qemu'

REGEXP = '/machine/qemu-[0-9]+-(.*)\\.libvirt-qemu'

UUID_1 = '123-456-789-1011'


class MockedDomain:
    """
    Mocked libvirt domain that contain only uuid string
    """
    def __init__(self, uuid_str):
        self.uuid_str = uuid_str

    def UUIDString(self):
        """
        mocked UUIDString method
        """
        return self.uuid_str


class MockedLibvirt:
    """
    Mocked libvirt client
    """
    def lookupByName(self, domain_name):
        """
        :return: MockedDomain with UUID_1
        """
        if domain_name == DOMAIN_NAME_1:
            return MockedDomain(UUID_1)
        raise libvirtError('')
