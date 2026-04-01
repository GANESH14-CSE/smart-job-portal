from django.contrib import admin
from .models import UserProfile, Job, Application, AnalysisResult

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'location', 'created_at')
    search_fields = ('user__username', 'user__email')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'employment_type', 'salary_max', 'fake_probability', 'is_active', 'posted_at')
    list_filter = ('employment_type', 'is_active')
    search_fields = ('title', 'company', 'skills_required')
    list_editable = ('is_active',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at')
    list_filter = ('status',)
    list_editable = ('status',)

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('application', 'ats_score', 'match_percentage', 'success_level', 'fake_probability', 'analyzed_at')
    list_filter = ('success_level',)
