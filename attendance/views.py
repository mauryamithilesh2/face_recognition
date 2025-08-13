# request
import cv2
import numpy as np
import face_recognition
from django.shortcuts import render,redirect,get_object_or_404
from .models import Student, Attendance,AdminProfile,Profile
from .face_encode import get_encode_faces
from datetime import date,timezone,datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from PIL import Image
from io import BytesIO
import base64
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.http import JsonResponse
import json
from .forms import StudentForm
from .forms import CustomUserCreationForm, Student,Teacher,AdminProfile
from django.urls import reverse










@login_required
def home(request):
    user = request.user

    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')

    elif hasattr(user, 'teacher'):
        return redirect('teacher_dashboard')

    elif hasattr(user, 'student'):
        return redirect('student_dashboard')

    else:
        return render(request, "attendance/home.html", {
            "role": "unknown"
        })


@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # auto create or ipdate profile
            profile,created=Profile.objects.get_or_create(user=user)

            if user.is_superuser or user.is_staff:
                profile.role='admin'
                profile.save()

            # Redirect logic
            if next_url:
                return redirect(next_url)
            elif profile.role == 'student':
                return redirect('student_dashboard')
            elif profile.role == 'teacher':
                return redirect('teacher_dashboard')
            elif profile.role == 'admin':
                return redirect('admin_dashboard') 
            else:
                return redirect('dashboard') 
        return render(request, 'attendance/login.html', {'error': 'Invalid credentials'})

    return render(request, 'attendance/login.html')

from django.http import HttpResponse

@login_required
def dashboard(request):
    try:
        role = request.user.profile.role
    except Profile.DoesNotExist:
        return render(request, 'error.html', {'message': 'Role not assigned'})

    if role == 'student':
        return redirect('student_dashboard')
    elif role == 'teacher':
        return render(request, 'attendance/teacher_dashboard.html', {'role': role})
    elif role == 'admin':
        return render(request, 'attendance/admin_dashboard.html', {'role': role})
    else:
        return HttpResponse("<h2>Access Denied</h2><p>You are not authorized to view this page.</p>")

@login_required
def teacher_dashboard(request):
    attendance_records = Attendance.objects.all()  # Or filter by class/teacher
    return render(request, 'attendance/teacher_dashboard.html', {'attendance_records': attendance_records})

from django.db.models import Prefetch

@login_required
def teacher_attendance_view(request):
    # Ensure the logged-in user is a teacher
    if request.user.profile.role != 'teacher':
        return render(request, 'error.html', {'message': 'Access denied: You are not authorized.'})

    # Fetch all students and their related attendance records
    students_with_attendance = Student.objects.prefetch_related(
        Prefetch('attendance_set', queryset=Attendance.objects.order_by('-timestamp'))
    )

    return render(request, 'attendance/teacher_all_attendance.html', {
        'students_with_attendance': students_with_attendance
    })



def is_student(user):
    return hasattr(user, 'profile') and user.profile.role == 'student'



from django.utils.timezone import localdate
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student, _ = Student.objects.get_or_create(user=request.user)
    records = Attendance.objects.filter(student=student).order_by('-timestamp')
    today=localdate()
    today_record=Attendance.objects.filter(student=student,timestamp__date=today).first()
    return render(request, "attendance/student_dashboard.html", {
        "records": records,
        "student": student,
        "today_record":today_record
    })
   


def is_admin(user):
    return user.is_staff

from django.http import HttpResponseForbidden
@user_passes_test(is_admin)
@login_required
def admin_dashboard(request):
    role = request.user.profile.role

    if role != 'admin':
        # Redirect based on role
        if role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('student_dashboard')
        else:
            return HttpResponseForbidden("Access Denied: Your role is not defne.")
    
    return render(request, 'attendance/admin_dashboard.html')

@login_required
@user_passes_test(is_admin)
def manage_students(request):
    students=Student.objects.all()
    return render(request,'Attendance/manage_students.html',{'students':students})


@login_required
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = Teacher.objects.all()
    return render(request, 'attendance/manage_teachers.html', {'teachers': teachers})



@staff_member_required
def admin_attendance_view(request):
    all_attendance =  Attendance.objects.select_related('student__user').all()
    
    return render(request, "attendance/admin_attendance.html", {
        "attendance_records": all_attendance
    })



@csrf_protect
def register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, request.FILES)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            role = user_form.cleaned_data['role']
            user.email = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password1'])  # 🔐 Very important!
            user.save()

            #  Set role after user is saved
            profile = Profile.objects.get(user=user)
            profile.role = role
            profile.save()

            # Save role-specific profile
            if role == 'student':
                Student.objects.create(user=user, image=user_form.cleaned_data.get('image'))
            elif role == 'teacher':
                Teacher.objects.create(user=user, image=user_form.cleaned_data.get('image'))
            elif role == 'admin':
                AdminProfile.objects.create(user=user, image=user_form.cleaned_data.get('image'))

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login_view')

        else:
            messages.error(request, "Please correct the errors.")
    else:
        user_form = CustomUserCreationForm()

    return render(request, 'attendance/register.html', {
        'user_form': user_form
    })


def logout_view(request):
    logout(request)
    return redirect('login_view')



@csrf_exempt
@user_passes_test(is_student)
@require_POST
@login_required
def mark_attendance(request):
    try:
        import json  # make sure json is imported
        data = json.loads(request.body)
        image_data = data.get('image')

        if not image_data:
            return JsonResponse({"error": "No image received"}, status=400)

        format, imgstr = image_data.split(';base64,') 
        img_bytes = base64.b64decode(imgstr)
        image = Image.open(BytesIO(img_bytes)).convert('RGB')

        frame = np.array(image)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        known_faces = get_encode_faces()
        known_names = list(known_faces.keys())
        known_encodings = list(known_faces.values())

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        
        if not face_encodings:
            return JsonResponse({"message": "No face detected ❗"})

        marked_names = []
        already_marked_names = []
        unrecognized_face = 0

        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding)
            face_distances = face_recognition.face_distance(known_encodings, encoding)

            if len(face_distances) > 0:
                best_match = np.argmin(face_distances)
                if matches[best_match]:
                    name = known_names[best_match]

                    if name != request.user.username:
                        return JsonResponse({"message": f"Face does not match logged-in user ❌"})
    
                    student = Student.objects.get(user=request.user)                    
                    today = timezone.localdate()
                    already_marked = Attendance.objects.filter(student=student, date=today).exists()

                    if already_marked:
                        already_marked_names.append(name)
                    else:
                        Attendance.objects.create(student=student, timestamp=timezone.now(), date=today)
                        marked_names.append(name)
                else:
                    unrecognized_face += 1
            else:
                unrecognized_face += 1
        # Prepare message
        if marked_names:
            return JsonResponse({"message": f"Attendance marked for: {', '.join(marked_names)} ✅"})
        elif already_marked_names:
            return JsonResponse({"message": f"Already marked: {', '.join(already_marked_names)} "})
        elif unrecognized_face > 0 :
            return JsonResponse({"message": "No recognized face found ❌"})
        else:
            return JsonResponse({"message": "unknown error ❗"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




# @login_required
# @user_passes_test(is_admin)
# def add_student(request):
#     if request.method=='POST':
#         form=StudentForm(request.POST)
#         if form.is_valid():
#             student=form.save()
#             return redirect('manage_students')
#     else:
#         form=StudentForm()

#     return render(request,'attendance/student_form.html',{'form':form,'action':'Add'})


@login_required
@user_passes_test(is_admin)
def edit_student(request,student_id):
    student=get_object_or_404(Student,id=student_id)
    form = StudentForm(request.POST or None ,instance=student)
    if form.is_valid():
        form.save()
        return redirect('manage_students')
    return render(request,'attendance/student_form.html',{'form':form,'action':'Edit'})


@login_required
@user_passes_test(is_admin)
def delete_student(request,student_id):
    student=get_object_or_404(Student,id=student_id)
    student.delete()
    return redirect('manage_students')