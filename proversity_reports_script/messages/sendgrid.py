"""
Sendrid client module.
"""
import copy
import traceback

from proversity_reports_script.messages.helpers import (
    generate_student_subplots,
    generate_graph,
    get_graph,
    format_learner_record,
    update_course_threshold,
)
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    From,
    To,
    FileContent,
    FileName,
    FileType,
    Disposition,
    TemplateId,
    Attachment,
    ContentId,
)

class SendGridSender:
    """
    Implementation to send messages using SendGrid.
    """

    def __init__(self, sg_api_key):
        self.api_client = SendGridAPIClient(sg_api_key)

    def build_message(self, **kwargs):
        """
        Return the message to deliver.
        """
        message = Mail()
        message.from_email = From(kwargs["sender"]["email"], kwargs["sender"]["name"])
        message.to = To(kwargs["receiver"]["email"])
        message.dynamic_template_data = kwargs["dynamic_template_data"]
        message.template_id = TemplateId(kwargs["template_id"])

        if kwargs["image_string"]:
            message.attachment = [
                Attachment(
                    FileContent(kwargs["image_string"]),
                    FileName('graph.png'),
                    FileType('image/png'),
                    Disposition('inline'),
                    ContentId(kwargs["graph_cid"])
                ),
            ]

        return message

    def send_message(self, message):
        """
        Deliver the message using SendGrip API.
        """
        if message:
            try:
                # build message and send it
                response = self.api_client.send(message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(str(e))

    def deliver_message_to_learners(self, data, extra_data):
        """
        Build and deliver message to learners.
        """
        for course_id, student_records  in data.items():
            for record in student_records:
                image_string = None
                record = format_learner_record(record)
                # calculate exact week per student
                metrics = copy.deepcopy(extra_data['metrics'])
                metrics, course_title = update_course_threshold(
                    extra_data.get('DATA_SOURCE'),
                    course_id,
                    '1',
                    metrics,
                )
                subplots_for_student = generate_student_subplots(record, metrics)
                metrics.clear()
                graph_generated = generate_graph(subplots=subplots_for_student)
                if graph_generated:
                    image_string = get_graph()
                if not image_string:
                    print("Not able to generate the graph")
                    continue
                receiver = {"email": record["email"]}
                dindata = {"name": record["username"], 'subject': "Week {}: {} Learning Tracker".format(1, course_title)}
                message_data = {
                    "image_string": image_string,
                    "sender": extra_data["SENDGRID_CONF"]["SENDER"],
                    "receiver" : receiver,
                    "dynamic_template_data": dindata,
                    "template_id": extra_data["SENDGRID_CONF"]["SENDGRID_TEMPLATE_ID"],
                    "graph_cid": extra_data["SENDGRID_CONF"]["SENDGRID_TEMPLATE_IMAGE_CID"],
                }
                message = self.build_message(**message_data)
                self.send_message(message)
