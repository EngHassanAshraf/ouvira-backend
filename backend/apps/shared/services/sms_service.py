import logging

from django.conf import settings
from rest_framework import response

from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
from vonage_http_client.errors import HttpRequestError

# from twilio.rest import Client
# from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str, from_number: str = None) -> bool:
    from_number = from_number or settings.TWILIO_PHONE_NUMBER
    # if you want to manage your secret, please do so by visiting your API Settings page in your dashboard
    try:
        client = Vonage(Auth(api_key=settings.VONAGE_KEY , api_secret=settings.VONAGE_API_SECRET))

        responseData:SmsResponse = client.sms.send(SmsMessage(to= phone, from_="Vonage APIs", text= message))

        if responseData.messages[0].status == "0":
            logger.info("SMS sent successfully to %s", phone)
            print("Message sent successfully.")
            return True
        else:
            logger.error("SMS failed to %s: %s", phone, response.messages[0].error_text)
            print("Message sent successfully.")
            return False

        # client = Client(
        #     settings.TWILIO_ACCOUNT_SID,
        #     settings.TWILIO_AUTH_TOKEN,
        # )
        # sms = client.messages.create(body=message, from_=from_number, to=phone)
        # return sms.sid

    # except TwilioRestException as e:
    #     logger.error("SMS failed to %s: %s", phone, e)
    #     return False

    except HttpRequestError as e:
        logger.error("SMS request error to %s: %s", phone, e)
        return False