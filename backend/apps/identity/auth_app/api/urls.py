from django.urls import path

from .views import (
    SignUPView,
    FinalizeSignInView,
    ResentOTPView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    Enable2FAView,
    TwoFAVerifyCodeView,
    TwoFAVerifyBackupView,
    SendOTPView,
    VerifyOTPView,
    ForgotPasswordView,
    ValidateResetTokenView,
    ResetPasswordView,
    ChangePasswordView,
)

urlpatterns = [
    # Signup endpoints
    path("signup/", SignUPView.as_view(), name="signup"),
    path("finalize-signin/", FinalizeSignInView.as_view(), name="finalize-signin"),

    # OTP endpoints
    path("resent-otp/", ResentOTPView.as_view(), name="resent-otp"),

    # Authentication endpoints
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),

    # 2FA endpoints
    path("settings_enable-2fa/", Enable2FAView.as_view(), name="enable-2fa"),
    path("login-2fa-verify-code/", TwoFAVerifyCodeView.as_view(), name="2fa-verify-code"),
    path("login-2fa-verify-backup/", TwoFAVerifyBackupView.as_view(), name="2fa-verify-backup"),

    # OTP (email + sms — channel auto-detected)
    path("otp/send/", SendOTPView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),

    # Password reset (unauthenticated)
    path("password/forgot/", ForgotPasswordView.as_view(), name="password-forgot"),
    path("password/validate-reset-token/", ValidateResetTokenView.as_view(), name="validate-reset-token"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),

    # Password change (authenticated)
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
]
