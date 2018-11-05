import pytest
from smartwatts.report import DepthLevel, extract, HWPCReportCore, HWPCReportSocket, HWPCReport


PATH_TO_TEST = "/smartwatts/test/"

"""
fake report
                    sensor

         groupA                 groupB
         id:1                   id:2

     SA         SB          SC          SD
     id:1      id:2        id:1        id:2

 CPUA  CPUB  CPUC  CPUD  CPUE  CPUF  CPUG  CPUH
 id:1  id:2  id:1  id:2  id:1  id:2  id:1  id:2  
 e0:0  e0:1  e0:2  e0:3  e1:0  e1:1  e1:2  e1:3
"""


def create_core_report(core_id, event_id, event_value):
    core = HWPCReportCore(core_id)
    core.events = {event_id : event_value}
    return core

def create_socket_report(socket_id, core_list):
    socket = HWPCReportSocket(socket_id)
    for core in core_list:
        socket.cores[core.core_id] = core
    return socket

def create_group_report(group_id, socket_list):
    group = {}
    for socket in socket_list:
        group[socket.socket_id] = socket
    return (group_id, group)

def create_report_root(group_list):
    sensor = HWPCReport(timestamp='time0', sensor='toto', target='system')
    for (group_id, group) in group_list:
        sensor.groups[group_id] = group
    return sensor


def core_report_assert(r1, r2):
    assert (r1.core_id == r2.core_id) and (r1.events == r2.events)

def socket_report_assert(r1, r2):
    assert r1.socket_id == r2.socket_id

    for (core_id, core_report) in r1.cores.items():
        assert core_id in r2.cores
        core_report_assert(core_report, r2.cores[core_id])


    for core_id in r2.cores:
        assert core_id in r1.cores

def report_assert(r1, r2):
    assert (r1.timestamp == r2.timestamp and r1.sensor == r2.sensor and
        r1.target == r2.target)


    for (group_id, group) in r1.groups.items():
        assert group_id in r2.groups
        for (socket_id, socket_report) in (r1.groups[group_id]).items():
            assert socket_id in r2.groups[group_id]
            socket_report_assert(socket_report,
                                       r2.groups[group_id][socket_id])

        for socket_id in r2.groups[group_id]:
            assert socket_id in r1.groups[group_id]

    for group_id in r2.groups:
        assert group_id in r2.groups


cpuA = create_core_report('1', 'e0', '0')
cpuB = create_core_report('2', 'e0', '1')
cpuC = create_core_report('1', 'e0', '2')
cpuD = create_core_report('2', 'e0', '3')
cpuE = create_core_report('1', 'e1', '0')
cpuF = create_core_report('2', 'e1', '1')
cpuG = create_core_report('1', 'e1', '2')
cpuH = create_core_report('2', 'e1', '3')

socketA = create_socket_report('1', [cpuA, cpuB])
socketB = create_socket_report('2', [cpuC, cpuD])
socketC = create_socket_report('1', [cpuE, cpuF])
socketD = create_socket_report('2', [cpuG, cpuH])

groupA = create_group_report('1', [socketA, socketB])
groupB = create_group_report('2', [socketC, socketD])

report = create_report_root([groupA, groupB])


class TestDatabase():

    def validate_reports(self, reports, validation_report_list,
                         validation_key_list):

        reports.sort(key=lambda x:x[0])
        
        validation_list = list(zip(validation_key_list, validation_report_list))
        validation_list.sort(key=lambda x:x[0])
        for ((key, report), (validation_key, validation_report)) in zip(
                reports, validation_list):
            assert key == validation_key
            report_assert(report, validation_report)

    def test_extract_root(self):
        extracted_reports = extract(report, DepthLevel.ROOT)

        assert len(extracted_reports) == 1
        [(key, extracted_report)] = extracted_reports
        assert key == (report.sensor,)
        report_assert(report, extracted_report)

    def test_extract_socket(self):
        extracted_reports = extract(report, DepthLevel.SOCKET)

        assert len(extracted_reports) == 2

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [socketA]),
             create_group_report('2', [socketC])
             ])

        report2 = create_report_root(
            [create_group_report('1', [socketB]),
             create_group_report('2', [socketD])
             ]
        )

        validation_report_list = [
            report1,
            report2
        ]

        validation_key_list = [
            (report.sensor, socketA.socket_id),
            (report.sensor, socketB.socket_id)
            ]
        self.validate_reports(extracted_reports, validation_report_list,
                              validation_key_list)



    def test_extract_core(self):
        extracted_reports = extract(report, DepthLevel.CORE)

        assert len(extracted_reports) == 4

        # Rapport 1
        report1 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1',[cpuA])
            ]),
             create_group_report('2', [
                 create_socket_report('1',[cpuE])
             ])
            ])

        report2 = create_report_root(
            [create_group_report('1', [
                create_socket_report('1',[cpuB])
            ]),
             create_group_report('2', [
                 create_socket_report('1',[cpuF])
             ])
            ])
        report3 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2',[cpuC])
            ]),
             create_group_report('2', [
                 create_socket_report('2',[cpuG])
             ])
            ])
                
        report4 = create_report_root(
            [create_group_report('1', [
                create_socket_report('2',[cpuD])
            ]),
             create_group_report('2', [
                 create_socket_report('2',[cpuH])
             ])
            ])

        validation_report_list = [
            report1,
            report2,
            report3,
            report4
        ]
        
        validation_key_list = [
            (report.sensor, socketA.socket_id, cpuA.core_id),
            (report.sensor, socketA.socket_id, cpuB.core_id),
            (report.sensor, socketB.socket_id, cpuC.core_id),
            (report.sensor, socketB.socket_id, cpuD.core_id)
            ]

        
        self.validate_reports(extracted_reports, validation_report_list,
                              validation_key_list)

                   
if __name__ == '__main__':
    unittest.main()
