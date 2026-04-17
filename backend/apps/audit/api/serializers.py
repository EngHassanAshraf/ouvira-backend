"""
Audit serializers for Notification, ActivityLog, and SecurityAuditLog.
"""
from rest_framework import serializers
from ..models import Notification, ActivityLog, SecurityAuditLog


class NotificationSerializer(serializers.ModelSerializer):
    """Full notification serializer."""

    class Meta:
        model = Notification
        fields = ["id", "user", "message", "read", "created_at"]
        read_only_fields = ["id", "user", "message", "created_at"]


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications."""

    class Meta:
        model = Notification
        fields = ["id", "message", "read", "created_at"]
        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):
    """Full activity log serializer — used for per-employee change history."""
    user_display = serializers.CharField(source="user.__str__", read_only=True)
    changed_fields = serializers.SerializerMethodField()

    def get_changed_fields(self, obj):
        """Return list of field names that changed (keys of new_values)."""
        if obj.new_values and isinstance(obj.new_values, dict):
            return list(obj.new_values.keys())
        return []

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "user_display",
            "company",
            "entity_type",
            "entity_id",
            "action",
            "changed_fields",
            "old_values",
            "new_values",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields


class ActivityLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing activity logs."""
    user_display = serializers.CharField(source="user.__str__", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user_display",
            "entity_type",
            "action",
            "created_at",
        ]
        read_only_fields = fields


class SecurityAuditLogSerializer(serializers.ModelSerializer):
    """Security audit log serializer."""
    user_display = serializers.CharField(source="user.__str__", read_only=True)

    class Meta:
        model = SecurityAuditLog
        fields = [
            "id",
            "user",
            "user_display",
            "date",
            "action",
            "metadata",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
