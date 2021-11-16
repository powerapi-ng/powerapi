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
import re
import logging

try:
    from libvirt import openReadOnly, libvirtError
except ImportError:
    logging.getLogger().info("libvirt-python is not installed.")

    class LibvirtException(Exception):
        """"""
        def __init__(self, _):
            Exception.__init__(self)

    libvirtError = LibvirtException
    openReadOnly = None

from powerapi.report_modifier.report_modifier import ReportModifier


class LibvirtMapper(ReportModifier):
    """
    Report modifier which modifi target with libvirt id by open stak uuid
    """

    def __init__(self, uri: str, regexp: str):
        self.regexp = re.compile(regexp)
        daemon_uri = None if uri == '' else uri
        self.libvirt = openReadOnly(daemon_uri)

    def modify_report(self, report):
        result = re.match(self.regexp, report.target)
        if result is not None:
            domain_name = result.groups(0)[0]
            try:
                domain = self.libvirt.lookupByName(domain_name)
                report.metadata["domain_id"] = domain.UUIDString()
            except libvirtError:
                pass
        return report
