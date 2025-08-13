from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Student, Teacher, AdminProfile

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    image = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'image']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['image','user','roll_no']

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['image', 'department']

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['image', 'access_level']


# class CustomUserCreationForm(UserCreationForm):
#     first_name = forms.CharField(max_length=30, required=True)
#     last_name = forms.CharField(max_length=30, required=True)

#     class Meta:
#         model = User
#         fields = ['username', 'first_name', 'last_name', 'password1', 'password2']
# class StudentForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields=['image']