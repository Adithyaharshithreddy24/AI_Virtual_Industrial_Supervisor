import os
from urllib.parse import quote

from twilio.rest import Client


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL")


client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)


def make_call(message: str, to_phone_number: str):
    """
    Make a Twilio voice call and speak the provided message.
    """

    try:
        # Encode message so it can safely be passed in the URL
        encoded_message = quote(message)

        # Twilio will request this URL after the call is answered
        twiml_url = (
            f"{PUBLIC_BACKEND_URL}/twiml"
            f"?message={encoded_message}"
        )

        call = client.calls.create(
            to=to_phone_number,
            from_=TWILIO_FROM_NUMBER,
            url=twiml_url
        )

        return {
            "success": True,
            "message": "Call initiated successfully",
            "call_sid": call.sid,
            "status": call.status
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }