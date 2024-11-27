from mailjet_rest import Client
import os
from dotenv import load_dotenv
import logging 
import httpx


load_dotenv()


api_key = os.getenv('MJ_APIKEY_PUBLIC')
api_secret = os.getenv('MJ_APIKEY_PRIVATE')


mailjet = Client(auth=(api_key, api_secret), version='v3.1')

async def send_general_notification_email(to_email, to_name, subject, content):
    """
    Sends a general notification email using Mailjet.

    :param to_email: Recipient's email address
    :param to_name: Recipient's name
    :param subject: Subject of the email
    :param content: Body of the email (can include plain text or HTML)
    :return: Tuple (status_code, response JSON)
    """
    # Validate inputs
    # if not to_email or not isinstance(to_email, str):
    #     logging.error(f"Invalid email: {to_email}")
    #     return None, {"error": "Invalid email"}
    # if not to_name or not isinstance(to_name, str):
    #     logging.error(f"Invalid name: {to_name}")
    #     return None, {"error": "Invalid name"}
    # if not subject or not isinstance(subject, str):
    #     logging.error(f"Invalid subject: {subject}")
    #     return None, {"error": "Invalid subject"}
    # if not content or not isinstance(content, str):
    #     logging.error(f"Invalid content: {content}")
    #     return None, {"error": "Invalid content"}

    # Prepare email payload
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "tennisdaddy.help@mail.bg",
                    "Name": "TennisDaddy"
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_name
                    }
                ],
                "Subject": subject,
                "TextPart": content,
            }
        ]
    }

    # Send email via Mailjet
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.mailjet.com/v3.1/send",
                auth=(api_key, api_secret),
                json=data
            )
            response.raise_for_status()  # Raise an error for non-2xx responses
            return response.status_code, response.json()
        except Exception as e:
            logging.error(f"Error sending email to {to_email}: {e}")
            return None, {"error": str(e)}
