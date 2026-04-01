import json, os, sys
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

JOBS = [
    dict(title="Senior Python Developer",company="TechNova Solutions",company_email="hr@technovasolutions.com",
         company_website="https://technovasolutions.com",location="Bangalore, Karnataka",employment_type="full_time",
         description="Experienced Python developer to build scalable APIs and microservices using Django and FastAPI. Collaborate with frontend and DevOps teams on real-world products.",
         requirements="3+ years Python, Django or FastAPI, PostgreSQL, Redis, Docker, Git, REST API",
         skills_required="Python, Django, FastAPI, PostgreSQL, Redis, Docker, Git, REST API",
         experience_required="3-5 years",salary_min=12,salary_max=22),
    dict(title="Full Stack Developer",company="CloudBase Technologies",company_email="careers@cloudbase.io",
         company_website="https://cloudbase.io",location="Hyderabad, Telangana",employment_type="full_time",
         description="Build next-generation SaaS applications with React frontend and Node.js backend. Integrate with cloud platforms.",
         requirements="2+ years React.js, Node.js, MongoDB or PostgreSQL, REST APIs, TypeScript, Git",
         skills_required="React, Node.js, TypeScript, MongoDB, GraphQL, AWS, Git, REST API",
         experience_required="2-4 years",salary_min=8,salary_max=18),
    dict(title="Data Scientist – ML and NLP",company="DataMind Analytics",company_email="talent@datamind.ai",
         company_website="https://datamind.ai",location="Mumbai, Maharashtra",employment_type="full_time",
         description="Work on NLP and machine learning projects. Develop and deploy models for production.",
         requirements="Python, scikit-learn, PyTorch or TensorFlow, NLP, BERT, Pandas, NumPy, SQL",
         skills_required="Python, Machine Learning, NLP, PyTorch, TensorFlow, spaCy, BERT, Pandas, NumPy, SQL",
         experience_required="2-4 years",salary_min=10,salary_max=25),
    dict(title="Django Backend Engineer",company="Fintech Ventures India",company_email="hr@fintechventures.in",
         company_website="https://fintechventures.in",location="Pune, Maharashtra",employment_type="full_time",
         description="Build and maintain Django REST APIs. Integrate payment gateways. Write clean tested code.",
         requirements="2+ years Django, Django REST Framework, MySQL or PostgreSQL, Redis, Celery, JWT",
         skills_required="Python, Django, Django REST Framework, MySQL, Redis, Celery, Docker, JWT",
         experience_required="2-3 years",salary_min=7,salary_max=15),
    dict(title="Software Development Intern",company="StartupHub Technologies",company_email="internships@startuphub.co",
         company_website="https://startuphub.co",location="Remote / Chennai",employment_type="internship",
         description="6-month internship for final-year students. Work on real projects alongside senior engineers.",
         requirements="Basic Python or JavaScript, HTML, CSS, Git knowledge",
         skills_required="Python, JavaScript, HTML, CSS, Git",
         experience_required="0-1 years",salary_min=1,salary_max=3),
    dict(title="DevOps Engineer",company="CloudOps Systems",company_email="hr@cloudopssystems.com",
         company_website="https://cloudopssystems.com",location="Bangalore, Karnataka",employment_type="full_time",
         description="Manage cloud infrastructure. Set up CI/CD pipelines and container orchestration on AWS.",
         requirements="3+ years DevOps, AWS, Docker, Kubernetes, Terraform, Jenkins, Linux",
         skills_required="AWS, Docker, Kubernetes, Terraform, Ansible, Jenkins, Linux, Git, CI/CD",
         experience_required="3-5 years",salary_min=15,salary_max=30),
    dict(title="Android Developer Kotlin",company="MobileFirst Studios",company_email="jobs@mobilefirststudios.com",
         company_website="https://mobilefirststudios.com",location="Delhi NCR",employment_type="full_time",
         description="Build Android apps using Kotlin. Implement MVVM architecture and integrate Firebase.",
         requirements="2+ years Android, Kotlin, Jetpack components, MVVM, Firebase, REST API, Git",
         skills_required="Android, Kotlin, Java, MVVM, Firebase, REST API, Git, Jetpack",
         experience_required="2-4 years",salary_min=8,salary_max=18),
    dict(title="Work From Home Earn 50k DEMO FAKE",company="EasyMoney Jobs",company_email="jobs@gmail.com",
         company_website="",location="Any Location",employment_type="part_time",
         description="No experience needed! Copy paste data earn guaranteed income. Immediate joining. No interview. Registration fee Rs 500.",
         requirements="No qualifications required.",
         skills_required="Copy Paste, Data Entry",
         experience_required="0 years",salary_min=30,salary_max=600),
]

class Command(BaseCommand):
    help = 'Seed database with sample jobs and admin user'

    def handle(self, *args, **kwargs):
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        if root not in sys.path: sys.path.insert(0, root)

        from jobportal.models import Job, UserProfile
        from ai_modules.keyword_matcher import detect_fake_job

        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin', email='admin@smartjobportal.com',
                password='admin123', first_name='Admin', last_name='User')
            UserProfile.objects.get_or_create(user=admin)
            self.stdout.write(self.style.SUCCESS('✅ Admin created  →  admin / admin123'))
        else:
            self.stdout.write('   Admin already exists.')

        admin_user = User.objects.get(username='admin')
        created = 0
        for jd in JOBS:
            if Job.objects.filter(title=jd['title'], company=jd['company']).exists():
                continue
            det = detect_fake_job(
                company=jd['company'], company_email=jd['company_email'],
                company_website=jd['company_website'], description=jd['description'],
                requirements=jd['requirements'], location=jd['location'],
                salary_min=jd['salary_min'], salary_max=jd['salary_max'])
            Job.objects.create(**jd, posted_by=admin_user,
                fake_probability=det['fake_probability'],
                fake_reasons=json.dumps(det['reasons']))
            created += 1
            self.stdout.write(f"  ✅ {jd['title']} @ {jd['company']}")

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Done! Created {created} jobs.'))
        self.stdout.write('  Open:  http://127.0.0.1:8000')
        self.stdout.write('  Admin: http://127.0.0.1:8000/admin  (admin / admin123)')
