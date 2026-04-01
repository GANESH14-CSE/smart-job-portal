from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, Job

class BasicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser',password='testpass123')

    def test_home_page(self):
        r = self.client.get('/')
        self.assertIn(r.status_code, [200,302])

    def test_job_create(self):
        job = Job.objects.create(
            title='Python Dev', company='TestCo',
            company_email='hr@testco.com', location='Bangalore',
            description='We need a Python developer with Django experience.',
            skills_required='Python, Django, SQL', posted_by=self.user)
        self.assertEqual(job.title, 'Python Dev')
        self.assertIn('Python', job.skills_list())

    def test_profile_created(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.assertEqual(profile.user.username, 'testuser')
