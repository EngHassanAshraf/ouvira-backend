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

app_name = "auth"

urlpatterns = [
    # --- Registration ---
    path("signup/", SignUPView.as_view(), name="signup"),
    path("finalize-signin/", FinalizeSignInView.as_view(), name="finalize-signin"),

    # --- Session ---
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),

    # --- OTP ---
    path("otp/send/", SendOTPView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("otp/resend/", ResentOTPView.as_view(), name="otp-resend"),

    # --- Two-factor authentication ---
    path("2fa/enable/", Enable2FAView.as_view(), name="2fa-enable"),
    path("2fa/verify/code/", TwoFAVerifyCodeView.as_view(), name="2fa-verify-code"),
    path("2fa/verify/backup/", TwoFAVerifyBackupView.as_view(), name="2fa-verify-backup"),

    # --- Password (unauthenticated flows) ---
    path("password/forgot/", ForgotPasswordView.as_view(), name="password-forgot"),
    path("password/validate-reset-token/", ValidateResetTokenView.as_view(), name="password-validate-reset-token"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),

    # --- Password (authenticated flows) ---
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
]
