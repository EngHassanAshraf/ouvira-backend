import logging

from django.conf import settings
from rest_framework import response

from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
from vonage_http_client.errors import HttpRequestError

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

import http.client
import json


logger = logging.getLogger(__name__)

# twilio (not working)
# def send_sms(phone: str, message: str, from_number: str = None) -> bool:
#     try:
#         client = Client(
#             settings.TWILIO_ACCOUNT_SID,
#             settings.TWILIO_AUTH_TOKEN,
#         )
#         from_number = from_number or settings.TWILIO_PHONE_NUMBER
#         sms = client.messages.create(body=message, from_=from_number, to=phone)
#         if sms.sid:
#             logger.info("SMS sent successfully to %s", phone)
#             return True
#         else:
#             logger.error("SMS failed to %s: %s", phone, sms.error_message)
#             return False
#     except TwilioRestException as e:
#         logger.error("SMS failed to %s: %s", phone, e)
#         return False

# vonage (too expensive)
# def send_sms(phone: str, message: str, from_number: str = None) -> bool:
#     # from_number = from_number or settings.TWILIO_PHONE_NUMBER
#     # if you want to manage your secret, please do so by visiting your API Settings page in your dashboard
#     try:
#         client = Vonage(Auth(api_key=settings.VONAGE_KEY , api_secret=settings.VONAGE_API_SECRET))
#         responseData:SmsResponse = client.sms.send(SmsMessage(to= phone, from_="Vonage APIs", text= message))
#         if responseData.messages[0].status == "0":
#             logger.info("SMS sent successfully to %s", phone)
#             return True
#         else:
#             logger.error("SMS failed to %s: %s", phone, responseData.messages[0].error_text)
#             return False
#     except HttpRequestError as e:
#         logger.error("SMS request error to %s: %s", phone, e)
#         return False

# infobip (the best)
def send_sms(phone: str, message: str, from_number: str = None) -> bool:
    try:
        conn = http.client.HTTPSConnection("vy3xve.api.infobip.com")
    except http.client.HTTPException as e:
        logger.error("HTTPException in Infobip connection: %s", e)
        logger.error("SMS sent failed to %s: %s", phone, e)
        return False
    except Exception as e:
        logger.error("Exception in Infobip connection: %s", e)
        logger.error("SMS sent failed to %s: %s", phone, e)
        return False

    payload = json.dumps({
        "messages": [
        {
            "destinations": [
                {
                    "to": phone
                }
            ],
            "sender": "ServiceSMS",
            "content": {
                "text": message
            }
        }
    ]
    })
    headers = {
    'Authorization': f'App {settings.INFOBIP_API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
    }
    
    try:
        conn.request("POST", "/sms/3/messages", payload, headers)
        res = conn.getresponse()
        data = res.read()
    except Exception as e:
        logger.error("Exception in Infobip response: %s", e)
        logger.error("SMS sent failed to %s: %s", phone, e)
        return False
    
    if res.status == 200:
        logger.info("SMS sent successfully to %s", phone)
        return True
    else:
        logger.error("SMS sent failed to %s: %s", phone, data.decode("utf-8"))
        return False