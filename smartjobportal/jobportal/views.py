import json, os, sys
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import UserProfile, Job, Application, AnalysisResult
from .forms import RegisterForm, ProfileForm, JobForm
from .serializers import JobSerializer, ApplicationSerializer, UserProfileSerializer, AnalysisResultSerializer

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)

from ai_modules.keyword_matcher import (
    extract_skills, get_missing_skills, get_skill_resources,
    run_full_analysis, detect_fake_job,
    predict_success, get_success_color, get_ats_grade,
)
from ai_modules.pdf_parser import extract_text_from_pdf


# ── HOME ──────────────────────────────────────────────────────────────────────
def home(request):
    recent_jobs = Job.objects.filter(is_active=True).order_by('-posted_at')[:6]
    return render(request, 'jobportal/home.html', {
        'recent_jobs':  recent_jobs,
        'total_jobs':   Job.objects.filter(is_active=True).count(),
        'total_users':  User.objects.count(),
    })

def about(request):
    tech_stack = [
        {'icon':'🐍','name':'Python 3.11','role':'Core language'},
        {'icon':'🎸','name':'Django 4.2','role':'Web framework'},
        {'icon':'🔌','name':'Django REST Framework','role':'API layer'},
        {'icon':'🧠','name':'spaCy','role':'NLP skill extraction'},
        {'icon':'🤖','name':'sentence-transformers','role':'BERT similarity'},
        {'icon':'📄','name':'PyMuPDF','role':'PDF extraction'},
        {'icon':'🗃️','name':'SQLite','role':'Database'},
        {'icon':'🎨','name':'Bootstrap 5','role':'Frontend UI'},
    ]
    return render(request, 'jobportal/about.html', {'tech_stack': tech_stack})


# ── AUTH ──────────────────────────────────────────────────────────────────────
def register(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Account created.')
            return redirect('dashboard')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=prof)
        if form.is_valid():
            form.save()
            request.user.first_name = request.POST.get('first_name','')
            request.user.last_name  = request.POST.get('last_name','')
            request.user.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=prof)
    return render(request, 'jobportal/profile.html', {'form': form, 'profile': prof})


# ── RESUME ────────────────────────────────────────────────────────────────────
@login_required
def upload_resume(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        f = request.FILES.get('resume')
        if not f:
            messages.error(request, 'Please select a file.'); return redirect('upload_resume')
        if not f.name.lower().endswith('.pdf'):
            messages.error(request, 'Only PDF files accepted.'); return redirect('upload_resume')
        if f.size > 5*1024*1024:
            messages.error(request, 'File must be under 5 MB.'); return redirect('upload_resume')
        prof.resume = f; prof.save()
        extracted = extract_text_from_pdf(prof.resume.path)
        if extracted.strip():
            skills = extract_skills(extracted)
            prof.resume_text = extracted; prof.skills = ', '.join(skills); prof.save()
            messages.success(request, f'Resume uploaded! Found {len(skills)} skills.')
        else:
            messages.warning(request, 'Uploaded but could not extract text. Use a text-based PDF.')
        return redirect('profile')
    return render(request, 'jobportal/upload_resume.html', {'profile': prof})


# ── JOBS ──────────────────────────────────────────────────────────────────────
def job_list(request):
    jobs  = Job.objects.filter(is_active=True)
    query = request.GET.get('q','')
    loc   = request.GET.get('location','')
    jtype = request.GET.get('type','')
    if query:
        jobs = jobs.filter(Q(title__icontains=query)|Q(company__icontains=query)|
                           Q(skills_required__icontains=query)|Q(description__icontains=query))
    if loc:   jobs = jobs.filter(location__icontains=loc)
    if jtype: jobs = jobs.filter(employment_type=jtype)
    applied_ids = []
    if request.user.is_authenticated:
        applied_ids = list(Application.objects.filter(
            applicant=request.user).values_list('job_id',flat=True))
    return render(request, 'jobportal/job_list.html', {
        'jobs':jobs,'applied_job_ids':applied_ids,
        'query':query,'location':loc,'job_type':jtype,'total':jobs.count(),
    })

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    has_applied, application = False, None
    if request.user.is_authenticated:
        application = Application.objects.filter(applicant=request.user,job=job).first()
        has_applied = application is not None
    return render(request, 'jobportal/job_detail.html', {
        'job':job,'skills_list':job.skills_list(),'fake_reasons':job.fake_reasons_list(),
        'has_applied':has_applied,'application':application,
    })

@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False); job.posted_by = request.user
            det = detect_fake_job(company=job.company,company_email=job.company_email,
                company_website=job.company_website,description=job.description,
                requirements=job.requirements,location=job.location,
                salary_min=job.salary_min,salary_max=job.salary_max)
            job.fake_probability = det['fake_probability']
            job.fake_reasons = json.dumps(det['reasons']); job.save()
            messages.success(request, f'Job "{job.title}" posted!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobForm()
    return render(request, 'jobportal/post_job.html', {'form': form})


# ── APPLY + AI ANALYSIS ───────────────────────────────────────────────────────
@login_required
def apply_job(request, job_id):
    job  = get_object_or_404(Job, id=job_id, is_active=True)
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if Application.objects.filter(applicant=request.user,job=job).exists():
        messages.info(request,'You already applied.'); return redirect('job_detail',job_id=job.id)
    if not prof.resume:
        messages.warning(request,'Upload your resume first.'); return redirect('upload_resume')
    if request.method == 'POST':
        app = Application.objects.create(
            applicant=request.user,job=job,
            cover_letter=request.POST.get('cover_letter',''))
        _run_ai_analysis(prof, job, app)
        messages.success(request,'Application submitted! View AI analysis below.')
        return redirect('analysis_result', application_id=app.id)
    return render(request,'jobportal/apply_job.html',{'job':job,'profile':prof})


def _run_ai_analysis(prof, job, app):
    resume_text = prof.resume_text or ''
    jd_text = f"{job.title} {job.description} {job.requirements} {job.skills_required}"
    r_skills = extract_skills(resume_text)
    j_skills = extract_skills(jd_text)
    all_jd   = list(set(j_skills + job.skills_list()))
    scores   = run_full_analysis(resume_text, jd_text, r_skills, all_jd)
    missing  = get_missing_skills(r_skills, all_jd)
    matched  = [s for s in all_jd if s not in missing]
    sugg = []
    if missing:    sugg.append(f"Add these skills: {', '.join(missing[:5])}")
    if scores['keyword_density'] < 50:     sugg.append("Use more keywords from the job description.")
    if scores['semantic_similarity'] < 40: sugg.append("Rewrite your summary to align with the role.")
    if scores['ats_score'] < 70:           sugg.append("Use standard headings: Experience, Education, Skills.")
    sugg.append("Quantify achievements (e.g. 'Improved speed by 30%') for more impact.")
    pred = predict_success(scores['ats_score'], scores['match_percentage'], len(missing))
    det  = detect_fake_job(company=job.company,company_email=job.company_email,
               company_website=job.company_website,description=job.description,
               requirements=job.requirements,location=job.location,
               salary_min=job.salary_min,salary_max=job.salary_max)
    AnalysisResult.objects.create(
        application=app,
        ats_score=scores['ats_score'], match_percentage=scores['match_percentage'],
        skill_match_score=scores['skill_match_score'],
        semantic_similarity=scores['semantic_similarity'],
        keyword_density=scores['keyword_density'],
        matched_skills=json.dumps(matched[:20]), missing_skills=json.dumps(missing[:20]),
        suggestions=json.dumps(sugg),
        success_probability=pred['success_probability'], success_level=pred['level'],
        success_explanation=pred['explanation'],
        fake_probability=det['fake_probability'], fake_reasons=json.dumps(det['reasons']),
    )


@login_required
def analysis_result(request, application_id):
    app      = get_object_or_404(Application, id=application_id, applicant=request.user)
    analysis = get_object_or_404(AnalysisResult, application=app)
    return render(request,'jobportal/analysis_result.html',{
        'application':app,'analysis':analysis,'job':app.job,
        'matched_skills':analysis.get_matched_skills(),
        'missing_skills':analysis.get_missing_skills(),
        'suggestions':   analysis.get_suggestions(),
        'fake_reasons':  analysis.get_fake_reasons(),
        'resources':     get_skill_resources(analysis.get_missing_skills()[:8]),
        'ats_grade':     get_ats_grade(analysis.ats_score),
        'success_color': get_success_color(analysis.success_level),
    })


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    apps = Application.objects.filter(
        applicant=request.user).select_related('job','analysis').order_by('-applied_at')
    total = apps.count(); avg_ats = 0; best = None
    if total:
        analyses = AnalysisResult.objects.filter(application__applicant=request.user)
        if analyses.exists():
            avg_ats = sum(a.ats_score for a in analyses)/analyses.count()
            best    = analyses.order_by('-ats_score').first()
    suggested = Job.objects.filter(is_active=True).exclude(
        id__in=apps.values_list('job_id',flat=True)).order_by('-posted_at')[:4]
    return render(request,'jobportal/dashboard.html',{
        'profile':prof,'applications':apps,'total_applied':total,
        'avg_ats':round(avg_ats,1),'best_match':best,'suggested_jobs':suggested,
    })


# ── REST API ──────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def api_job_list(request):
    jobs = Job.objects.filter(is_active=True)
    q    = request.query_params.get('q','')
    jt   = request.query_params.get('type','')
    if q:  jobs = jobs.filter(Q(title__icontains=q)|Q(company__icontains=q)|Q(skills_required__icontains=q))
    if jt: jobs = jobs.filter(employment_type=jt)
    return Response({'count':jobs.count(),'results':JobSerializer(jobs,many=True).data})

@api_view(['GET'])
@permission_classes([AllowAny])
def api_job_detail(request, job_id):
    return Response(JobSerializer(get_object_or_404(Job,id=job_id,is_active=True)).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_apply_job(request, job_id):
    job  = get_object_or_404(Job,id=job_id,is_active=True)
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if not prof.resume: return Response({'error':'Upload resume first.'},status=400)
    if Application.objects.filter(applicant=request.user,job=job).exists():
        return Response({'error':'Already applied.'},status=400)
    app = Application.objects.create(
        applicant=request.user,job=job,
        cover_letter=request.data.get('cover_letter',''))
    _run_ai_analysis(prof,job,app)
    a = app.analysis
    return Response({
        'message':'Application submitted.','application_id':app.id,
        'ats_score':a.ats_score,'match_percentage':a.match_percentage,
        'success_probability':a.success_probability,'success_level':a.success_level,
        'fake_probability':a.fake_probability,
        'matched_skills':a.get_matched_skills(),'missing_skills':a.get_missing_skills(),
        'suggestions':a.get_suggestions(),
    },status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_resume(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    f = request.FILES.get('resume')
    if not f: return Response({'error':'No file.'},status=400)
    if not f.name.lower().endswith('.pdf'): return Response({'error':'PDF only.'},status=400)
    prof.resume = f; prof.save()
    text = extract_text_from_pdf(prof.resume.path)
    skills = extract_skills(text)
    prof.resume_text = text; prof.skills = ', '.join(skills); prof.save()
    return Response({'message':'Uploaded.','skills_found':skills,'count':len(skills)})

@api_view(['POST'])
@permission_classes([AllowAny])
def api_analyze(request):
    rt = request.data.get('resume_text','')
    jd = request.data.get('jd_text','')
    if not rt or not jd: return Response({'error':'Both resume_text and jd_text required.'},status=400)
    rs = extract_skills(rt); js = extract_skills(jd)
    scores = run_full_analysis(rt,jd,rs,js)
    missing = get_missing_skills(rs,js)
    pred = predict_success(scores['ats_score'],scores['match_percentage'],len(missing))
    return Response({**scores,'resume_skills':rs,'missing_skills':missing,
                     'prediction':pred,'resources':get_skill_resources(missing[:5])})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    apps = Application.objects.filter(
        applicant=request.user).select_related('job','analysis').order_by('-applied_at')
    return Response(ApplicationSerializer(apps,many=True).data)

@api_view(['GET','PATCH'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'PATCH':
        for f in ('phone','location','bio'):
            if f in request.data: setattr(prof,f,request.data[f])
        prof.save()
    return Response(UserProfileSerializer(prof).data)
