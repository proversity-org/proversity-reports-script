import abc


class AbstractBaseReportBackend(object):
    """
    Abstract Base Class for custom Proversity's reports.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        pass


    @abc.abstractmethod
    def json_report_to_csv(self, json_report_data={}):
        """
        Process json data to convert into csv format.
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def create_csv_file(self, course, body_dict):
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
