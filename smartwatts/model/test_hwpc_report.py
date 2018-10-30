import unittest
from model import DepthLevel, extract, HWPCReportCore, HWPCReportSocket, HWPCReport


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


def create_core(core_id, event_id, event_value):
    core = HWPCReportCore(core_id)
    core.events = {event_id : event_value}
    return core

def create_socket(socket_id, core_list):
    socket = HWPCReportSocket(socket_id)
    for core in core_list:
        socket.cores[core.core_id] = core
    return socket

def create_group(group_id, socket_list):
    group = {}
    for socket in socket_list:
        group[socket.socket_id] = socket
    return (group_id, group)

def create_sensor(group_list):
    sensor = HWPCReport(timestamp='time0', sensor='toto', target='system')
    for (group_id, group) in group_list:
        sensor.groups[group_id] = group
    return sensor

def gen_sensor():

    cpuA = create_core('1', 'e0', '0')
    cpuB = create_core('2', 'e0', '1')
    cpuC = create_core('1', 'e0', '2')
    cpuD = create_core('2', 'e0', '3')
    cpuE = create_core('1', 'e1', '0')
    cpuF = create_core('2', 'e1', '1')
    cpuG = create_core('1', 'e1', '2')
    cpuH = create_core('2', 'e1', '3')

    socketA = create_socket('1', [cpuA, cpuB])
    socketB = create_socket('2', [cpuC, cpuD])
    socketC = create_socket('1', [cpuE, cpuF])
    socketD = create_socket('2', [cpuG, cpuH])

    groupA = create_group('1', [socketA, socketB])
    groupB = create_group('2', [socketC, socketD])

    return create_sensor([groupA, groupB])

class TestExtract(unittest.TestCase):

    def test_extract_sensor(self):
        report = gen_sensor()
        # print(report.groups['1']['1'])
        for _, r in extract(report, DepthLevel.CORE):
            print('=========================================')
            print(r)
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()
