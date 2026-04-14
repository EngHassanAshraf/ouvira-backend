import hmac
import hashlib
from datetime import timedelta
from django.utils.timezone import now
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

from apps.identity.auth_app.models import OTPRecord
from apps.identity.auth_app.tests.base import BaseAuthTestCase
from apps.identity.auth_app.services.otp_service import OTPService, OTP_ATTEMPTS_KEY


class OTPVerificationTests(BaseAuthTestCase):
    """
    Tests for the OTP send and verify endpoints.
    Covers the required scenarios:
    - 5 failed attempts locks identifier
    - Successful verify clears counter, sets verified
    - Expired returns 400
    - Resubmitting same OTP returns error (single use)
    """

    def setUp(self):
        super().setUp()
        self.send_url = reverse("v1:auth:otp-send")
        self.verify_url = reverse("v1:auth:otp-verify")
        self.identifier = "testuser@ouvira.app"
        # Clear cache between tests to isolate rate limits / locks
        cache.clear()

    def test_5_failed_attempts_locks_identifier(self):
        """OTP: 5 failed attempts locks the identifier — 6th attempt rejected even with correct OTP"""
        # Create a valid OTP record
        raw_otp = "123456"
        otp_hash = hmac.new(
            settings.SECRET_KEY.encode(),
            raw_otp.encode(),
            hashlib.sha256
        ).hexdigest()
        OTPRecord.objects.create(
            identifier=self.identifier,
            channel="email",
            otp_hash=otp_hash,
            expires_at=now() + timedelta(minutes=10)
        )

        # 5 failed attempts with wrong OTP
        wrong_otp_payload = {"identifier": self.identifier, "otp": "000000"}
        for _ in range(5):
            response = self.client.post(self.verify_url, wrong_otp_payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data["message"], "invalid_or_expired_otp")
        
        from unittest.mock import patch
        with patch("rest_framework.throttling.ScopedRateThrottle.allow_request", return_value=True):
            # 6th attempt with WRONG OTP should fail with 429
            response = self.client.post(self.verify_url, wrong_otp_payload, format="json")
            self.assertEqual(response.status_code, 429)
            self.assertIn("otp_locked", response.data["message"])
            self.assertIn("15 minutes", response.data["message"])
            
            # 7th attempt with CORRECT OTP should also fail with 429
            correct_otp_payload = {"identifier": self.identifier, "otp": raw_otp}
            response2 = self.client.post(self.verify_url, correct_otp_payload, format="json")
            self.assertEqual(response2.status_code, 429)
            self.assertIn("otp_locked", response2.data["message"])

    def test_successful_verify_clears_counter_sets_verified(self):
        """OTP: Successful verify sets is_verified=True and clears the Redis attempt counter"""
        raw_otp = "123456"
        # Since testing generate_and_send involves the real SECRET_KEY, let's use the service
        # to generate it to ensure hashing matches exactly.
        OTPService.generate_and_send(self.identifier)
        
        # Sneak in and grab the raw OTP. Since we generate randomly, let's just 
        # override the DB record hash with one we know.
        record = OTPRecord.objects.get(identifier=self.identifier)
        from django.conf import settings
        record.otp_hash = OTPService._compute_hash(raw_otp) if hasattr(OTPService, '_compute_hash') else hmac.new(
            settings.SECRET_KEY.encode(), 
            raw_otp.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        # Actually instead of guessing SECRET_KEY, let's just use the app's exact compute method
        from django.conf import settings
        record.otp_hash = hmac.new(settings.SECRET_KEY.encode(), raw_otp.encode(), hashlib.sha256).hexdigest()
        record.save()

        # Simulate 2 failed attempts
        cache_key = OTP_ATTEMPTS_KEY.format(identifier=self.identifier)
        cache.set(cache_key, 2)

        # Submit correct OTP
        response = self.client.post(self.verify_url, {"identifier": self.identifier, "otp": raw_otp}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")

        # Check DB: is_verified=True
        record.refresh_from_db()
        self.assertTrue(record.is_verified)

        # Check Cache: counter cleared
        self.assertIsNone(cache.get(cache_key))

    def test_expired_otp_returns_400(self):
        """OTP: Expired OTP returns invalid_or_expired_otp (not 500, not expired_otp separately)"""
        raw_otp = "123456"
        from django.conf import settings
        otp_hash = hmac.new(settings.SECRET_KEY.encode(), raw_otp.encode(), hashlib.sha256).hexdigest()
        
        # Create an expired record
        OTPRecord.objects.create(
            identifier=self.identifier,
            channel="email",
            otp_hash=otp_hash,
            expires_at=now() - timedelta(minutes=1)
        )

        response = self.client.post(self.verify_url, {"identifier": self.identifier, "otp": raw_otp}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "invalid_or_expired_otp")
        # Ensure it got deleted!
        self.assertFalse(OTPRecord.objects.filter(identifier=self.identifier).exists())

    def test_otp_single_use(self):
        """OTP is single-use — resubmitting the same correct OTP after success returns error"""
        raw_otp = "654321"
        from django.conf import settings
        otp_hash = hmac.new(settings.SECRET_KEY.encode(), raw_otp.encode(), hashlib.sha256).hexdigest()
        
        OTPRecord.objects.create(
            identifier=self.identifier,
            channel="email",
            otp_hash=otp_hash,
            expires_at=now() + timedelta(minutes=10)
        )

        # Attempt 1: Success
        response1 = self.client.post(self.verify_url, {"identifier": self.identifier, "otp": raw_otp}, format="json")
        self.assertEqual(response1.status_code, 200)

        # Attempt 2: Resubmit same correct OTP
        response2 = self.client.post(self.verify_url, {"identifier": self.identifier, "otp": raw_otp}, format="json")
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.data["message"], "invalid_or_expired_otp")
