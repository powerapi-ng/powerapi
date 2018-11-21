"""
Module hwpc_model
"""

from smartwatts.report_model import ReportModel, KEYS_CSV_COMMON, KEYS_COMMON


class HWPCModel(ReportModel):
    """
    HWPCModel class.
    It define all the function for get the hwpc necessary field from
    any kind of database.
    """

    def from_mongodb(self, json):
        """ Override """
        final_dict = {}
        final_dict['groups'] = {}

        for key, val in json.items():
            if key in KEYS_COMMON:
                final_dict[key] = val
            else:
                final_dict['groups'][key] = val
        return final_dict

    def from_csvdb(self, file_name, row):
        """ Override """
        final_dict = {key: row[key] for key in KEYS_COMMON}
        final_dict['groups'] = {}

        # If group doesn't exist, create it
        if file_name not in final_dict:
            final_dict['groups'][file_name] = {}

        # If socket doesn't exist, create it
        if row['socket'] not in final_dict['groups'][file_name]:
            final_dict['groups'][file_name][row['socket']] = {}

        # If cpu doesn't exist, create it
        if row['cpu'] not in final_dict['groups'][file_name][row['socket']]:
            final_dict['groups'][file_name][row['socket']][row['cpu']] = {}

        # Add events
        for key, value in row.items():
            if key not in KEYS_CSV_COMMON:
                final_dict['groups'][file_name][
                    row['socket']][row['cpu']][key] = int(value)

        return final_dict
