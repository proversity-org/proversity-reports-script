
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


encoded_string = None
script_dir = os.path.dirname(__file__)
rel_path = "progress_graph.png"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('ascii')


class MessageSender:
    """
    Client Class
    Product enviar el correo con la imagen (parse data) usando x cliente
    """

    def send(self, ):
        pass

    def _get_sender(sender):
        if sender == 'sengrid':
            return SendGridSender


class SendGridSender:
    """
    Producto class

    """

    def __init__(self, sg_api_key):
        "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'"
        self.api_client = SendGridAPIClient(sg_api_key)
        self.message = None

    def build_message(self, **kwargs):

        self.message = Mail()
        self.message.from_email = From(kwargs["sender"]["email"], kwargs["sender"]["name"])
        self.message.to = To("diego.millan@edunext.co", "Pearson learner tracker")
        self.message.dynamic_template_data = {
            'name': 'Diego Millan',
            'subject': "Learning tracker progress"
        }
        self.message.template_id = TemplateId('d-7144fea70bdd4c48b04af931357cdf42')
        self.message.attachment = [
            Attachment(
                FileContent(encoded_string),
                FileName('graph.png'),
                FileType('image/png'),
                Disposition('inline'),
                ContentId("r4nd0mc0nt3nt")
            ),
        ]

    def build_json(self):
        self.message = {
            "attachments": [
                {
                    "content": encoded_string,
                    "content_id": "r4nd0mc0nt3nt",
                    "disposition": "inline",
                    "filename": "graph.png",
                    "name": "graph",
                    "type": "png"
                }
            ],
            "from": {
                "email": "pearson@example.com",
                "name": "Pearson Type"
            },
            "mail_settings": {
                "footer": {
                    "enable": True,
                    "html": "<p>Thanks</br>The SendGrid Team Footerrrrrr</p>",
                    "text": "Thanks,/n The SendGrid Team"
                },
                "sandbox_mode": {
                    "enable": False
                },
                "spam_check": {
                    "enable": True,
                    "post_to_url": "http://example.com/compliance",
                    "threshold": 3
                }
            },
            "personalizations": [
                {
                    "to": [
                        {
                            "email": "diego.millan@edunext.co",
                            "name": "John Doe"
                        }
                    ],
                    "substitutions": {
                        "-name-": "Example User"
                    },
                    "subject": "I'm replacing the subject tag"
                }
            ],
            "subject": "Learning tracker progress",
            "template_id": "d-7144fea70bdd4c48b04af931357cdf42"
        }

        print ("json built")

    def send_message(self):
        """
        """
        if self.message:
            try:
                response = self.api_client.send(self.message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(str(e))

    def send_dummy(self):

        self.message = Mail(
            to_emails='diego.millan@edunext.co'
        )
        self.message.from_email = From("pearson-edx@test.com", "Pearson learner tracker")
        self.message.dynamic_template_data = {
            'name': 'Diego Millan',
            'subject': "Learning tracker progress"
        }
        self.message.template_id = TemplateId('d-7144fea70bdd4c48b04af931357cdf42')
        self.message.attachment = [
            Attachment(
                FileContent(encoded_string),
                FileName('graph.png'),
                FileType('image/png'),
                Disposition('inline'),
                ContentId("r4nd0mc0nt3nt")
            ),
        ]
        if self.message:
            try:
                response = self.api_client.send(self.message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(str(e))

    def get_data(self):
        data = {
            "sender": {"email": "pearsonx@example.com", "name": "PearsonX"}
        }
        return data
