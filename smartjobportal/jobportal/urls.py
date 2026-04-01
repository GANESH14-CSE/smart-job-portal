from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('',                               views.home,            name='home'),
    path('about/',                         views.about,           name='about'),
    path('register/',                      views.register,        name='register'),
    path('profile/',                       views.profile,         name='profile'),
    path('dashboard/',                     views.dashboard,       name='dashboard'),
    path('upload-resume/',                 views.upload_resume,   name='upload_resume'),

    # Jobs
    path('jobs/',                          views.job_list,        name='job_list'),
    path('jobs/post/',                     views.post_job,        name='post_job'),
    path('jobs/<int:job_id>/',             views.job_detail,      name='job_detail'),
    path('jobs/<int:job_id>/apply/',       views.apply_job,       name='apply_job'),

    # Analysis
    path('analysis/<int:application_id>/', views.analysis_result, name='analysis_result'),

    # REST API
    path('api/jobs/',                      views.api_job_list,      name='api_job_list'),
    path('api/jobs/<int:job_id>/',         views.api_job_detail,    name='api_job_detail'),
    path('api/apply/<int:job_id>/',        views.api_apply_job,     name='api_apply_job'),
    path('api/upload-resume/',             views.api_upload_resume, name='api_upload_resume'),
    path('api/analyze/',                   views.api_analyze,       name='api_analyze'),
    path('api/dashboard/',                 views.api_dashboard,     name='api_dashboard'),
    path('api/profile/',                   views.api_profile,       name='api_profile'),
]
