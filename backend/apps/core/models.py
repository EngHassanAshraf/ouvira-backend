from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Default manager that excludes soft-deleted records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Unfiltered manager — includes soft-deleted records. Use explicitly."""

    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Default manager hides soft-deleted rows
    objects = SoftDeleteManager()
    # Escape hatch when you genuinely need deleted rows
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
