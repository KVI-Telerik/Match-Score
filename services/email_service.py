from mailjet_rest import Client
import os
from dotenv import load_dotenv
import logging 


load_dotenv()


api_key = os.getenv('MJ_APIKEY_PUBLIC')
api_secret = os.getenv('MJ_APIKEY_PRIVATE')


mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_general_notification_email(to_email, to_name, subject, content):
    """
    Sends a general notification email using Mailjet.

    :param to_email: Recipient's email address
    :param to_name: Recipient's name
    :param subject: Subject of the email
    :param content: Body of the email (can include plain text or HTML)
    :return: Tuple (status_code, response JSON)
    """
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "your_email@example.com",  # Replace with a verified sender email
                    "Name": "Your App Name"  # Replace with your app/service name
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_name
                    }
                ],
                "Subject": subject,
                "TextPart": content,  # Text-only content
                "HTMLPart": f"<p>{content.replace('\n', '<br>')}</p>"  # HTML content
            }
        ]
    }
    try:
        result = mailjet.send.create(data=data)
        return result.status_code, result.json()
    except Exception as e:
        # Handle exceptions such as network issues or invalid API credentials
        logging.error(f"Error sending email to {to_email}: {e}")