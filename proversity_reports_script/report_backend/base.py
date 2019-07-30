"""
Abstract base class for openedx-proversity-reports.
"""
import abc


class AbstractBaseReportBackend(object):
    """
    Abstract Base Class for custom Proversity's reports.
    """
    __metaclass__ = abc.ABCMeta
    spreadsheet_data = []

    def __init__(self, spreadsheet_data):
        self.spreadsheet_data = spreadsheet_data


    @abc.abstractmethod
    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def create_csv_file(self, file_name, body_dict, headers, spreadsheet_id):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to the implemented storage.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        raise NotImplementedError()
