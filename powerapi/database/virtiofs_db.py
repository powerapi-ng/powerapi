import re
import os

from typing import List

from powerapi.database import BaseDB, DBError

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

    def __init__(self, vm_name_regexp: str, root_directory_name: str, vm_directory_name_prefix = '' : str, vm_directory_name_suffix = '' : str):
        """
        :param vm_name_regexp:           regexp used to extract vm name from report. The regexp must match the name of the target in the HWPC-report and a group must 
        :param root_directory_name:      directory where VM directory will be stored
        :param vm_directory_name_prefix: first part of the VM directory name
        :param vm_directory_name_suffix: last part of the VM directory name
        """
        BaseDB.__init__(self)

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

    def save(self, report: Report, report_model: ReportModel):
        directory_name = self._generate_vm_directory_name(report.target)
        if name is None:
            return

        vm_filename, power = report_model.to_virtiofs_db(report)
        vm_filename_path =self.root_directory_name + '/' + directory_name + '/' vm_filename
        if not os.path.exists(vm_filename_path):
            raise DirectoryDoesNotExistForVirtioFS(vm_filename_path)

        vm_file = open(vm_filename_path, 'w+')
        vm_file.write(str(power))
        vm_file.close()

    def save_many(self, reports: List[Report], report_model: ReportModel):
        for report in reports:
            self.save(report, report_model)
