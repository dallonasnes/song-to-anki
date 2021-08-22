# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(subject, content):
    message = Mail(
        from_email="dallon.asnes@gmail.com",
        to_emails="songtoankilogging@gmail.com",
        subject=str(subject)
        + " on {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        html_content=str(content),
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        # print(response.status_code)
        # print(response.body)
        # print(response.headers)
    except Exception as e:
        print(str(e))
