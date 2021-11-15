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

from mock import patch

try:
    from libvirt import libvirtError
except ImportError:
    libvirtError = Exception

from powerapi.report_modifier import LibvirtMapper
from powerapi.report import Report

from powerapi.test_utils.libvirt import MockedLibvirt
from powerapi.test_utils.libvirt import DOMAIN_NAME_1, LIBVIRT_TARGET_NAME1, LIBVIRT_TARGET_NAME2, UUID_1, REGEXP


BAD_TARGET = 'lkjqlskjdlqksjdlkj'

@pytest.fixture
def libvirt_mapper():
    with patch('powerapi.report_modifier.libvirt_mapper.openReadOnly', return_value=MockedLibvirt()):
        return LibvirtMapper('', REGEXP)


def test_modify_report_that_not_match_regexp_musnt_modify_report(libvirt_mapper):
    report = Report(0, 'sensor', BAD_TARGET)
    new_report = libvirt_mapper.modify_report(report)
    assert new_report.target == BAD_TARGET


def test_modify_report_that_match_regexp_must_modify_report(libvirt_mapper):
    report = Report(0, 'sensor', LIBVIRT_TARGET_NAME1)
    new_report = libvirt_mapper.modify_report(report)
    assert new_report.target == UUID_1


def test_modify_report_that_match_regexp_but_with_wrong_domain_name_musnt_modify_report(libvirt_mapper):
    report = Report(0, 'sensor', LIBVIRT_TARGET_NAME2)
    new_report = libvirt_mapper.modify_report(report)
    assert new_report.target == LIBVIRT_TARGET_NAME2
