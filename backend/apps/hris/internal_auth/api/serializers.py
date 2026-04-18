"""
Internal Auth Serializers
=========================
Input validation only — no business logic.
"""
from rest_framework import serializers


class InternalLoginSerializer(serializers.Serializer):
    """
    Input serializer for POST /api/v1/hris/internal/auth/login/

    Fields:
        identifier  — email or username (required)
        password    — raw password (required, write-only)
        company_id  — optional explicit company context for multi-company users
    """

    identifier = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
        help_text="Email address or username.",
    )
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Account password.",
    )
    company_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Optional. Specify which company to log into for users "
            "who belong to multiple companies."
        ),
    )

    def validate_identifier(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Identifier cannot be blank.")
        return value

    def validate_password(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Password cannot be blank.")
        return value


class InternalLogoutSerializer(serializers.Serializer):
    """Input serializer for POST /api/v1/hris/internal/auth/logout/"""

    refresh_token = serializers.CharField(
        help_text="The refresh token to blacklist.",
    )
