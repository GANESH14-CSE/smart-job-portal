import json
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone       = models.CharField(max_length=15, blank=True)
    location    = models.CharField(max_length=100, blank=True)
    bio         = models.TextField(blank=True)
    resume      = models.FileField(upload_to='resumes/', blank=True, null=True)
    resume_text = models.TextField(blank=True)
    skills      = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]


class Job(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time','Full Time'), ('part_time','Part Time'),
        ('internship','Internship'), ('contract','Contract'), ('remote','Remote'),
    ]
    title               = models.CharField(max_length=200)
    company             = models.CharField(max_length=200)
    company_email       = models.EmailField()
    company_website     = models.URLField(blank=True)
    location            = models.CharField(max_length=100)
    employment_type     = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    description         = models.TextField()
    requirements        = models.TextField(blank=True)
    skills_required     = models.TextField()
    experience_required = models.CharField(max_length=50, default='0-1 years')
    salary_min          = models.PositiveIntegerField(default=0)
    salary_max          = models.PositiveIntegerField(default=0)
    posted_by           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    is_active           = models.BooleanField(default=True)
    posted_at           = models.DateTimeField(auto_now_add=True)
    deadline            = models.DateField(null=True, blank=True)
    fake_probability    = models.FloatField(default=0.0)
    fake_reasons        = models.TextField(blank=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.title} at {self.company}"

    def skills_list(self):
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def fake_reasons_list(self):
        try:    return json.loads(self.fake_reasons)
        except: return []


class Application(models.Model):
    STATUS = [
        ('applied','Applied'), ('under_review','Under Review'),
        ('shortlisted','Shortlisted'), ('rejected','Rejected'), ('hired','Hired'),
    ]
    applicant    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job          = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS, default='applied')
    applied_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('applicant', 'job')

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title}"


class AnalysisResult(models.Model):
    application         = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='analysis')
    ats_score           = models.FloatField(default=0.0)
    match_percentage    = models.FloatField(default=0.0)
    skill_match_score   = models.FloatField(default=0.0)
    semantic_similarity = models.FloatField(default=0.0)
    keyword_density     = models.FloatField(default=0.0)
    matched_skills      = models.TextField(blank=True)
    missing_skills      = models.TextField(blank=True)
    suggestions         = models.TextField(blank=True)
    success_probability = models.FloatField(default=0.0)
    success_level       = models.CharField(max_length=10, default='Low')
    success_explanation = models.TextField(blank=True)
    fake_probability    = models.FloatField(default=0.0)
    fake_reasons        = models.TextField(blank=True)
    analyzed_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis: {self.application}"

    def get_matched_skills(self):
        try:    return json.loads(self.matched_skills)
        except: return []

    def get_missing_skills(self):
        try:    return json.loads(self.missing_skills)
        except: return []

    def get_suggestions(self):
        try:    return json.loads(self.suggestions)
        except: return []

    def get_fake_reasons(self):
        try:    return json.loads(self.fake_reasons)
        except: return []
