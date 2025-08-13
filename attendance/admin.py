from django.contrib import admin

# Register your models here.
from .models import Student,Attendance

admin.site.register(Student)
admin.site.register(Attendance)

