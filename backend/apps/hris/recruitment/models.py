from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel

class JobPost(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hris_recruitment_job_posts"

class Applicant(TimeStampedModel, SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    resume = models.FileField(upload_to="resumes/")
    applied_job = models.ForeignKey(JobPost, on_delete=models.CASCADE)

    class Meta:
        db_table = "hris_recruitment_applicants"