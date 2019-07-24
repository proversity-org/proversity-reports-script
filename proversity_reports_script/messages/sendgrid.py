
# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python

import base64
import os
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
        "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''"
        self.api_client = SendGridAPIClient(sg_api_key)

    def build_message(self, **kwargs):

        message = Mail()
        message.from_email = From(kwargs["sender"]["email"], kwargs["sender"]["name"])
        message.to = To("diego.millan@edunext.co", "Pearson learner tracker")
        message.dynamic_template_data = {
            'name': 'Diego Millan',
            'subject': "Learning tracker progress"
        }
        message.template_id = TemplateId('d-7144fea70bdd4c48b04af931357cdf42')

        if kwargs["image_string"]:
            message.attachment = [
                Attachment(
                    FileContent(kwargs["image_string"]),
                    FileName('graph.png'),
                    FileType('image/png'),
                    Disposition('inline'),
                    ContentId("r4nd0mc0nt3nt")
                ),
            ]

        return message

    def send_message(self):
        """
        Deliver the message using SendGrip API
        """
        if self.message:
            try:
                # build message and send it
                response = self.api_client.send(self.message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(str(e))
            finally:
                # clean images
                pass


    def get_data(self):
        """
        TODO
        """

        data = {
            "sender": {"email": "pearsonx3@example.com", "name": "PearsonX3"}
        }

        image_string = self.get_image()
        if image_string:
            data["image_string"] = image_string

        return data

    def get_image(self):
        """
        TODO
        """
        encoded_string = None
        try:
            script_dir = os.path.dirname(__file__)
            rel_path = "images/output.png"
            abs_file_path = os.path.join(script_dir, rel_path)
            with open(abs_file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        except Exception as identifier:
            return None
        else:
            return encoded_string



