from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    HiringRequest, HiringRequestApproval, JobAdvertisement,
    Candidate, JobApplication, Interview, CandidateDocument,
    JobOffer, Onboarding, PostProbationEvaluation
)

class HiringRequestApprovalInline(admin.TabularInline):
    model = HiringRequestApproval
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(HiringRequest)
class HiringRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_title', 'department', 'vacancies', 'status', 'created_at')
    list_filter = ('status', 'company', 'department')
    search_fields = ('job_title__title', 'purpose')
    inlines = [HiringRequestApprovalInline]
    actions = ['submit_requests']

    def submit_requests(self, request, queryset):
        queryset.update(status='submitted')
    submit_requests.short_description = _("Submit selected hiring requests")

@admin.register(JobAdvertisement)
class JobAdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'hiring_request', 'status', 'deadline', 'published_at')
    list_filter = ('status', 'hiring_request__company')
    search_fields = ('title', 'description')

class CandidateDocumentInline(admin.TabularInline):
    model = CandidateDocument
    extra = 0

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'company')
    list_filter = ('company',)
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    inlines = [CandidateDocumentInline]

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job_advertisement', 'status', 'classification', 'applied_at')
    list_filter = ('status', 'classification', 'job_advertisement__hiring_request__company')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'interview_type', 'interview_date', 'status', 'average_score')
    list_filter = ('status', 'interview_type', 'interview_date')
    search_fields = ('application__candidate__first_name', 'application__candidate__last_name')
    date_hierarchy = 'interview_date'

@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ('application', 'salary', 'start_date', 'status', 'sent_at')
    list_filter = ('status', 'start_date')
    search_fields = ('application__candidate__first_name', 'application__candidate__last_name')

@admin.register(Onboarding)
class OnboardingAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'status')
    list_filter = ('status',)
    search_fields = ('candidate__first_name', 'candidate__last_name')

@admin.register(PostProbationEvaluation)
class PostProbationEvaluationAdmin(admin.ModelAdmin):
    list_display = ('application', 'evaluation_date', 'performance_score', 'decision')
    list_filter = ('decision', 'evaluation_date')
    search_fields = ('application__candidate__first_name', 'application__candidate__last_name')

@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'doc_type', 'status', 'created_at')
    list_filter = ('status', 'doc_type')
    search_fields = ('candidate__first_name', 'candidate__last_name')
