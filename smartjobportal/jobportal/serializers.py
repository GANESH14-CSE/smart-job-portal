from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Job, Application, AnalysisResult

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    username  = serializers.CharField(source='user.username', read_only=True)
    email     = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    skills_list = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id','username','email','full_name','phone','location','bio','skills','skills_list','resume','created_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_skills_list(self, obj):
        return obj.skills_list()

class JobSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.SerializerMethodField()
    employment_type_display = serializers.SerializerMethodField()
    skills_list = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id','title','company','company_email','company_website','location',
                  'employment_type','employment_type_display','description','requirements',
                  'skills_required','skills_list','experience_required','salary_min','salary_max',
                  'is_active','posted_at','deadline','fake_probability','posted_by_name','applications_count']

    def get_posted_by_name(self, obj):
        return obj.posted_by.get_full_name() or obj.posted_by.username

    def get_employment_type_display(self, obj):
        return obj.get_employment_type_display()

    def get_skills_list(self, obj):
        return obj.skills_list()

    def get_applications_count(self, obj):
        return obj.applications.count()

class AnalysisResultSerializer(serializers.ModelSerializer):
    matched_skills = serializers.SerializerMethodField()
    missing_skills = serializers.SerializerMethodField()
    suggestions    = serializers.SerializerMethodField()
    fake_reasons   = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisResult
        fields = ['id','ats_score','match_percentage','skill_match_score','semantic_similarity',
                  'keyword_density','matched_skills','missing_skills','suggestions',
                  'success_probability','success_level','success_explanation',
                  'fake_probability','fake_reasons','analyzed_at']

    def get_matched_skills(self, obj): return obj.get_matched_skills()
    def get_missing_skills(self, obj): return obj.get_missing_skills()
    def get_suggestions(self, obj):    return obj.get_suggestions()
    def get_fake_reasons(self, obj):   return obj.get_fake_reasons()

class ApplicationSerializer(serializers.ModelSerializer):
    job_title      = serializers.CharField(source='job.title',   read_only=True)
    company        = serializers.CharField(source='job.company', read_only=True)
    location       = serializers.CharField(source='job.location',read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    analysis       = AnalysisResultSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id','job','job_title','company','location','cover_letter',
                  'status','status_display','applied_at','analysis']
