from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Job, Application

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'First Name'}))
    last_name = forms.CharField(max_length=30, required=True,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Last Name'}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email'}))

    class Meta:
        model = User
        fields = ('first_name','last_name','username','email','password1','password2')
        widgets = {'username': forms.TextInput(attrs={'class':'form-control','placeholder':'Username'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class':'form-control','placeholder':'Password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm Password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit: user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone','location','bio')
        widgets = {
            'phone':    forms.TextInput(attrs={'class':'form-control','placeholder':'Phone Number'}),
            'location': forms.TextInput(attrs={'class':'form-control','placeholder':'City, State'}),
            'bio':      forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Brief bio...'}),
        }

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('title','company','company_email','company_website','location',
                  'employment_type','description','requirements','skills_required',
                  'experience_required','salary_min','salary_max','deadline')
        widgets = {
            'title':               forms.TextInput(attrs={'class':'form-control'}),
            'company':             forms.TextInput(attrs={'class':'form-control'}),
            'company_email':       forms.EmailInput(attrs={'class':'form-control'}),
            'company_website':     forms.URLInput(attrs={'class':'form-control'}),
            'location':            forms.TextInput(attrs={'class':'form-control'}),
            'employment_type':     forms.Select(attrs={'class':'form-select'}),
            'description':         forms.Textarea(attrs={'class':'form-control','rows':5}),
            'requirements':        forms.Textarea(attrs={'class':'form-control','rows':4}),
            'skills_required':     forms.TextInput(attrs={'class':'form-control','placeholder':'Python, Django, SQL'}),
            'experience_required': forms.TextInput(attrs={'class':'form-control'}),
            'salary_min':          forms.NumberInput(attrs={'class':'form-control'}),
            'salary_max':          forms.NumberInput(attrs={'class':'form-control'}),
            'deadline':            forms.DateInput(attrs={'class':'form-control','type':'date'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('cover_letter',)
        widgets = {'cover_letter': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'Cover letter (optional)...'})}
