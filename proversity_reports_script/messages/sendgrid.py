"""
Sendrid client module.
"""

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
        Deliver the message using SendGrip API
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
