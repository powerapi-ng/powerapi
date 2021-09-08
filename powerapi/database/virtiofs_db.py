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
import re
import os

from typing import List, Type

from powerapi.report import Report
from .base_db import BaseDB, DBError


class DirectoryDoesNotExistForVirtioFS(DBError):
    """
    Error raised when root or VM directory does not eist
    """
    def __init__(self, directory):
        DBError.__init__(self, 'No such file or directory : ' + directory)


class VirtioFSDB(BaseDB):
    """
    write power consumption of virtual machine in a file shared with the virtual machine

    The File will be written in a directory created by the VM manager.

    A regular expression must be given by the VM manager to extract vm name from target name. VM name is used to find directory that contains the output file.
    """
    def __init__(self, report_type: Type[Report], vm_name_regexp: str, root_directory_name: str,
                 vm_directory_name_prefix: str = '', vm_directory_name_suffix: str = ''):
        """
        :param vm_name_regexp:           regexp used to extract vm name from report. The regexp must match the name of the target
                                         in the HWPC-report and a group must
        :param root_directory_name:      directory where VM directory will be stored
        :param vm_directory_name_prefix: first part of the VM directory name
        :param vm_directory_name_suffix: last part of the VM directory name
        """
        BaseDB.__init__(self, report_type)

        self.vm_name_regexp = re.compile(vm_name_regexp)
        self.root_directory_name = root_directory_name
        self.vm_directory_name_suffix = vm_directory_name_suffix
        self.vm_directory_name_prefix = vm_directory_name_prefix

    def _generate_vm_directory_name(self, target):
        match = re.match(self.vm_name_regexp, target)
        if match is None:
            return None
        vm_name = match.groups()[0]
        return self.vm_directory_name_prefix + vm_name + self.vm_directory_name_suffix

    def connect(self):
        if not os.path.exists(self.root_directory_name):
            raise DirectoryDoesNotExistForVirtioFS(self.root_directory_name)

    def save(self, report: Report):
        directory_name = self._generate_vm_directory_name(report.target)
        if directory_name is None:
            return

        vm_filename, power = self.report_type.to_virtiofs_db(report)
        vm_filename_path = self.root_directory_name + '/' + directory_name + '/'
        if not os.path.exists(vm_filename_path):
            raise DirectoryDoesNotExistForVirtioFS(vm_filename_path)

        vm_file = open(vm_filename_path + vm_filename, 'w+')
        vm_file.write(str(power))
        vm_file.close()

    def save_many(self, reports: List[Report]):
        for report in reports:
            self.save(report)
