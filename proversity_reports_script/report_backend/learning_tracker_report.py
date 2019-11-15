"""
Report backend for learning tracker report.
"""
import csv
import json

import boto3

from proversity_reports_script.messages.helpers import (
    download_from_data_source,
    get_course_threshold,
)
from proversity_reports_script.messages.sendgrid import SendGridSender
from proversity_reports_script.report_backend.base import AbstractBaseReportBackend


class LearningTrackerReportBackend(AbstractBaseReportBackend):
    """
    Backend for learning tracker report.
    """

    THRESHOLD_FILE_PATH='ltr-targets.csv'

    def __init__(self, *args, **kwargs):
        extra_data = kwargs.get('extra_data', {})
        super(LearningTrackerReportBackend, self).__init__(extra_data.get('SPREADSHEET_DATA', {}))
        self.lt_extra_data = extra_data
        self.data_source_conf = self.lt_extra_data.get("DATA_SOURCE", {})

        # check if its working with external learners
        # amazon_settings = extra_data.get('AWS_DATA', {})
        # self.amazon_bucket = amazon_settings.get('amazon_bucket', '')
        # self.file_prefix = amazon_settings.get('file_prefix', '')
        # donde se usan las de arriba??? chequear y consolidar en DATA_SOURCE

    def generate_report(self, json_report_data):
        """
        Main logic to generate the report.
        """
        if json_report_data.get('status') != 'SUCCESS':
            return None

        # Update report with external courses data
        # report_data.update(self._get_edx_courses_data_from_csv())

        # check received data
        report_data = json_report_data.get('result', {})
        print(json.dumps(report_data))

        # Now download required files
        threshold_internal_courses = download_from_data_source(
            self.data_source_conf.get('threshold_internal_courses')
        )
        threshold_external_courses = download_from_data_source(
            self.data_source_conf.get('threshold_external_courses')
        )
        learner_data_external_courses = download_from_data_source(
            self.data_source_conf.get('learner_data_external_courses')
        )

        # Calling helper to send notifications
        self._send_notifications(report_data)

    def json_report_to_csv(self, json_report_data):
        """
        Process json data to convert into csv format.
        """
        raise NotImplementedError()

    def create_csv_file(self, course, body_dict, spreadsheet_id):
        """
        Creates the csv file with the passed arguments, and then save it locally.
        """
        raise NotImplementedError()

    def upload_file_to_storage(self, course, path_file):
        """
        Uploads the csv report, to S3 storage.
        """
        raise NotImplementedError()

    def _get_edx_courses_data_from_csv(self):
        """
        Gets csv file from S3 and extracts the data.
        """
        amazon_resource = boto3.resource('s3')
        amazon_bucket = amazon_resource.Bucket(self.amazon_bucket)
        amazon_client = boto3.client('s3')
        previous = None
        data = {}

        for amazon_object in amazon_bucket.objects.filter(Prefix=self.file_prefix):

            if not previous or amazon_object.last_modified > previous:
                key = amazon_object.key

            previous = amazon_object.last_modified

        with open('aws-file.csv', 'wb') as csv_data:
            amazon_client.download_fileobj(self.amazon_bucket, key, csv_data)
            csv_data.close()
        with open('aws-file.csv', 'r') as csv_data:
            dict_reader = csv.DictReader(csv_data)
            for row in dict_reader:
                course_id = row['course_id']
                course_data = data.get(course_id, [])
                current_grade = row.get('current_grade', '0')
                user_id = row.get('id', '')

                user_data = {
                    'username': row.get('user_username', ''),
                    'email': row.get('user_email', ''),
                    'user_id': int(user_id) if user_id else user_id,
                    'cumulative_grade': float(current_grade) if current_grade else 0,
                    'has_verified_certificate': row.get('has_passed', 'False') == 'True',
                }
                course_data.append(user_data)
                data[course_id] = course_data

        return data

    def _send_notifications(self, data):
        """
        Method in charge of delivering the learning tracker message.
        """
        sendgrid_conf = self.lt_extra_data.get("SENDGRID_CONF")
        sender = SendGridSender(sendgrid_conf.get("API_KEY"))
        sender.deliver_message_to_learners(data, self.lt_extra_data)
