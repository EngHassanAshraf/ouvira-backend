import hmac
import hashlib
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.conf import settings

from apps.identity.auth_app.models import OTPRecord
from apps.identity.auth_app.services.otp_service import OTPService, OTP_ATTEMPTS_KEY, MAX_ATTEMPTS
from apps.identity.auth_app.services.auth_service import AuthService
from apps.identity.account.models.user import CustomUser
from apps.shared.exceptions import BusinessException


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class OTPFlowTests(TestCase):
    def setUp(self):
        self.phone = "+201012345678"
        self.email = "test@example.com"
        cache.clear()

        # Create base user for auth_service integration
        self.user = CustomUser.objects.create(
            username="testuser",
            primary_mobile=self.phone,
            email=self.email
        )

    @patch("apps.identity.auth_app.services.otp_service.secrets.randbelow")
    @patch("apps.shared.services.sms_service.send_sms")
    def test_generate_and_send_hmac_hashing(self, mock_sms, mock_rand):
        """Ensure OTP is securely generated, hashed via HMAC, and stored without plaintext."""
        mock_rand.return_value = 23456  # Produces OTP 123456 (23456 + 100000)
        
        OTPService.generate_and_send(self.phone)

        record = OTPRecord.objects.get(identifier=self.phone)
        
        # Verify the actual hash stored against the expected HMAC string
        expected_hash = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            b"123456",
            hashlib.sha256
        ).hexdigest()
        
        self.assertEqual(record.otp_hash, expected_hash)
        self.assertFalse(record.is_verified)
        mock_sms.assert_called_once()

    @patch("apps.identity.auth_app.services.otp_service.secrets.randbelow")
    @patch("apps.shared.services.sms_service.send_sms")
    def test_auth_service_integration_success(self, mock_sms, mock_rand):
        """Test full sequence coordinating OTP verify and user model updates."""
        mock_rand.return_value = 23456
        OTPService.generate_and_send(self.phone)
        
        self.assertFalse(self.user.phone_verified)
        
        # Call verification through the new AuthService flow
        user = AuthService.verify_user_otp(self.phone, "123456")
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)
        self.assertEqual(user.pk, self.user.pk)
        
        record = OTPRecord.objects.get(identifier=self.phone)
        self.assertTrue(record.is_verified)

    @patch("apps.identity.auth_app.services.otp_service.secrets.randbelow")
    @patch("apps.shared.services.sms_service.send_sms")
    def test_redis_lockout_mechanism(self, mock_sms, mock_rand):
        """Ensure Redis triggers lockout after exactly MAX_ATTEMPTS invalid entries."""
        mock_rand.return_value = 23456
        OTPService.generate_and_send(self.phone)
        
        # Simulate wrong OTPs to strictly increment the Redis counter to MAX_ATTEMPTS
        for _ in range(MAX_ATTEMPTS):
            with self.assertRaises(BusinessException) as e:
                OTPService.verify(self.phone, "000000")
            self.assertIn("invalid_or_expired_otp", str(e.exception))
            
        # The next attempt, EVEN IF THE OTP IS CORRECT, must raise the time-based lock
        with self.assertRaises(BusinessException) as e:
            OTPService.verify(self.phone, "123456")
        self.assertIn("locked", str(e.exception))
        
        # Ensure Redis accurately reflects the maximum threshold state
        attempts_key = OTP_ATTEMPTS_KEY.format(identifier=self.phone)
        self.assertEqual(cache.get(attempts_key), MAX_ATTEMPTS)
