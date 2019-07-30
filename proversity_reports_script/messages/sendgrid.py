"""
Sendrid client module.
"""

from proversity_reports_script.messages.helpers import (
    generate_student_subplots,
    generate_graph,
    get_graph,
)
from proversity_reports_script.messages.data_configs import (
    settings
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

    def deliver_message_to_learners(self, message, data):
        """
        Build and deliver message to learners.
        """
        for course_id, student_records  in data.items():
            for record in student_records:
                image_string = None
                subplots_for_student = generate_student_subplots(record, settings["LEARNER_TRACKER_REPORT"]["metrics"])
                graph_generated = generate_graph(subplots=subplots_for_student)
                if graph_generated:
                    image_string = get_graph()
                if not image_string:
                    continue
                receiver = {"email": record["email"]}
                dindata = {"name": record["username"], 'subject': "Week {}: {} Learning Tracker".format(1, course_id)}
                message_data = {
                    "image_string": image_string,
                    "sender": settings["SENGRID_CONF"]["SENDER"],
                    "receiver" : receiver,
                    "dynamic_template_data": dindata,
                    "template_id": settings["LEARNER_TRACKER_REPORT"]["SENDRID_TEMPLATE_ID"],
                    "graph_cid": settings["LEARNER_TRACKER_REPORT"]["SENDRID_TEMPLATE_IMAGE_CID"],
                }
                message = self.build_message(**message_data)
                self.send_message(message)
