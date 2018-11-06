"""
Module hwpc_sensor which define the HWPCReport class
"""
from smartwatts.report.report import Report
import smartwatts.utils as utils


class HWPCReportCore(Report):
    """
    HWPCReportCore class
    Encapuslation for core report
    """

    def __init__(self, core_id=None):
        Report.__init__(self, core_id)
        self.core_id = core_id
        self.events = {}

    def __str__(self):
        display = ("  \n" +
                   '    ' + self.core_id + ":\n" +
                   '    ' + self.events.__str__() + "\n")
        return display

    def feed_from_csv(self, csv, group):
        """ Define how to feed the object from csv input """
        keys = list(csv.keys())
        values = list(csv.values())
        self.events = {
            keys[i]: values[i] for i in range(5, len(keys))}

    def feed_from_mongodb(self, json):
        """ Define how to feed the object from mongodb input """
        self.events = json


class HWPCReportSocket(Report):
    """
    HWPCReportSocket class
    Encapsulation for Socket report
    """
    def __init__(self, socket_id):
        """
        socket:            socket id (int)
        cores:             dict of cores
        """
        Report.__init__(self, socket_id)
        self.socket_id = socket_id
        self.cores = {}
        self.group_id = None

    def get_child_reports(self):
        return [report for report in self.cores.values()]

    def set_child_report(self, key, val):
        self.cores[key] = val

    def cut_child(self):
        socket_report = HWPCReportSocket(self.socket_id)
        # socket_report.hw_id = self.hw_id
        socket_report.group_id = self.group_id
        return socket_report

    def __str__(self):
        display = (" \n" +
                   '  ' + self.socket_id + ":\n" +
                   '  ' + ''.join([self.cores[c].__str__()
                                   for c in self.cores]))
        return display

    def feed_from_csv(self, csv, group):
        """ Define how to feed the object from csv input """
        if csv['cpu'] not in self.cores:
            self.cores[csv['cpu']] = (
                HWPCReportCore(csv['cpu']))
        self.cores[csv['cpu']].feed_from_csv(csv, group)

    def feed_from_mongodb(self, json):
        """ Define how to feed the object from mongodb input """
        cores = list(json.keys())

        for core in cores:
            if core not in self.cores:
                self.cores[core] = HWPCReportCore(core)
            self.cores[core].feed_from_mongodb(json[core])


class HWPCReport(Report):
    """ HWPCReport class """

    def __init__(self, timestamp=None, sensor=None, target=None):
        """
        timestamp: when the report is done
        sensor:    sensor name
        target:    target name
        groups:    dict of group, a group is a dict of socket
        rapl:      dict of rapl ground truth
        """
        Report.__init__(self, sensor)
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target
        self.groups = {}
        self.rapl = {}

    def get_child_reports(self):

        reports = []
        for (group_id, sockets) in self.groups.items():
            for (_, socket_report) in sockets.items():
                socket_report.group_id = group_id
                reports.append(socket_report)
        return reports

    def set_child_report(self, key, val):
        socket_id = key
        socket_report = val

        if socket_report.group_id not in self.groups:
            self.groups[socket_report.group_id] = {}
        self.groups[socket_report.group_id][socket_id] = socket_report

    def cut_child(self):
        return HWPCReport(self.timestamp, self.sensor, self.target)

    def __str__(self):
        display = ("\n" +
                   ' ' + str(self.timestamp) + "\n" +
                   ' ' + self.sensor + "\n" +
                   ' ' + self.target + "\n" +
                   ' ' + self.rapl.__str__() + "\n" +
                   ' '.join(['\n' + g + '\n ' +
                             ''.join([self.groups[g][s].__str__()
                                      for s in self.groups[g]])
                             for g in self.groups]) +
                   "\n")
        return display

    def feed_from_csv(self, csv, group):
        """ Define how to feed the object from csv input """
        if (self.timestamp is None or
                self.sensor is None or
                self.target is None):
            self.timestamp = int(csv['timestamp'])
            self.sensor = csv['sensor']
            self.target = csv['target']

        """ If it's RAPL and a unknown socket """
        if group == 'rapl' and csv['socket'] not in self.rapl:
            keys = list(csv.keys())
            values = list(csv.values())
            self.rapl[csv['socket']] = {
                keys[i]: values[i] for i in range(5, len(csv))}
        else:
            if group not in self.groups:
                self.groups[group] = {}

            if csv['socket'] not in self.groups[group]:
                self.groups[group][csv['socket']] = (
                    HWPCReportSocket(csv['socket']))

            self.groups[group][csv['socket']].feed_from_csv(csv, group)

    def feed_from_mongodb(self, json):
        """ Define how to feed the object from mongodb input """
        if (self.timestamp is None or
                self.sensor is None or
                self.target is None):
            self.timestamp = utils.datetime_to_timestamp(json['timestamp'])
            self.sensor = json['sensor']
            self.target = json['target']

        """ If target are not the same, we stop here """
        if self.target != json['target']:
            return

        """ If it's RAPL report """
        if 'rapl' in json:
            self.target = None
            self.rapl = json['rapl']
        else:
            keys = list(json.keys())
            """ On cherche les groupes définit dans le rapport """
            for group in keys:

                """
                On passe si on trouve une entrée qui n'est pas
                un groupe
                """
                if group in ['_id', 'sensor', 'target', 'timestamp']:
                    continue

                """ Si le groupe n'existe pas, on le crée """
                if group not in self.groups:
                    self.groups[group] = {}

                """
                Pour chaque socket du groupe, on crée un
                nouveau HWPCReportSocket et on le feed
                """
                sockets = list(json[group].keys())
                for socket in sockets:
                    if socket not in self.groups[group]:
                        self.groups[group][socket] = (
                            HWPCReportSocket(socket))
                    self.groups[group][socket].feed_from_mongodb(
                        json[group][socket])
