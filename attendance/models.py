from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time
# Create your models here.

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=True)  # 🔹 Added field

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='teachers/', blank=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='admins/', blank=True)
    access_level = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='student_images/', blank=True, null=True)  # Optional
    roll_no = models.CharField(max_length=20,unique=True,null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}({self.roll_no })"

class Attendance(models.Model):
    STATUS_CHOICES=[
        ('Present','Present'),
        ('Absent','Absent'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    timestamp = models.DateTimeField(default=timezone.now)
    status=models.CharField(max_length=10,choices=STATUS_CHOICES, default='Present')

    class Meta:
        unique_together = ('student', 'date')
        ordering=['-date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.status}"
