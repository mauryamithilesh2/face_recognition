# request
import cv2
import numpy as np
import face_recognition
from django.shortcuts import render,redirect,get_object_or_404
from .models import Student, Attendance,AdminProfile,Profile,Teacher
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
from django.http import JsonResponse,HttpResponse,HttpResponseForbidden
import json
from .forms import StudentForm
from .forms import CustomUserCreationForm
from django.urls import reverse
from django.db.models import Prefetch
from django.http import HttpResponseForbidden


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
        return render(request, "attendance/home.html", {"role": "unknown"})


@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=username, password=password)
        if user:
            profile, created = Profile.objects.get_or_create(user=user)

            # ❌ Block unapproved admins
            if profile.role == 'admin' and not profile.is_approved:
                return render(request, 'attendance/login.html', {
                    'error': 'Your admin account is awaiting approval.'
                })

            login(request, user)

            if user.is_superuser or user.is_staff:
                profile.role = 'admin'
                profile.is_approved = True
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
    attendance_records = Attendance.objects.all()
    return render(request, 'attendance/teacher_dashboard.html', {'attendance_records': attendance_records})


@login_required
def teacher_attendance_view(request):
    if request.user.profile.role != 'teacher':
        return render(request, 'error.html', {'message': 'Access denied: You are not authorized.'})

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
    today = localdate()
    today_record = Attendance.objects.filter(student=student, timestamp__date=today).first()
    return render(request, "attendance/student_dashboard.html", {
        "records": records,
        "student": student,
        "today_record": today_record
    })


def is_admin(user):
    return user.is_staff



@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    role = request.user.profile.role

    if role != 'admin':
        if role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('student_dashboard')
        else:
            return HttpResponseForbidden("Access Denied: Your role is not defined.")

    # ✅ Get pending admin approval requests
    pending_admins = Profile.objects.filter(role='admin', is_approved=False)

    # ✅ Handle Approve/Reject from the same dashboard
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        profile = get_object_or_404(Profile, user__id=user_id, role='admin')

        if action == 'approve':
            profile.is_approved = True
            profile.save()
            messages.success(request, f"{profile.user.username} approved as admin ")
        elif action == 'reject':
            profile.user.delete()
            messages.warning(request, "Admin request rejected ")

        return redirect('admin_dashboard')

    return render(request, 'attendance/admin_dashboard.html', {
        "pending_admins": pending_admins
    })

@login_required
@user_passes_test(is_admin)
def manage_students(request):
    students = Student.objects.all()
    return render(request, 'attendance/manage_students.html', {'students': students})


@login_required
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = Teacher.objects.all()
    return render(request, 'attendance/manage_teachers.html', {'teachers': teachers})

from collections import defaultdict
@staff_member_required
def admin_attendance_view(request):
    students = Student.objects.select_related('user').all()
    all_attendance = Attendance.objects.select_related('student__user').order_by(
        'student__user__username', '-date'
        )
    grouped_attendance = defaultdict(list)

    for record in all_attendance:
        grouped_attendance[record.student].append(record)

    # ⬇️ must be OUTSIDE the loop
    final_group = {}
    for student in students:
        final_group[student] = grouped_attendance.get(student, [])
    return render(request, "attendance/admin_attendance.html", {
         "grouped_attendance": final_group
    })


@csrf_protect
def register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, request.FILES)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            role = user_form.cleaned_data['role']
            user.email = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password1'])
            user.save()

            profile = Profile.objects.get(user=user)
            profile.role = role

            # Students & teachers auto-approved
            if role in ['student', 'teacher']:
                profile.is_approved = True
            else:
                profile.is_approved = False  # admins must wait

            profile.save()

            if role == 'student':
                Student.objects.create(user=user, image=user_form.cleaned_data.get('image'))
            elif role == 'teacher':
                Teacher.objects.create(user=user, image=user_form.cleaned_data.get('image'))
            elif role == 'admin':
                AdminProfile.objects.create(user=user, image=user_form.cleaned_data.get('image'))
                messages.info(request, "Admin registration submitted. Awaiting approval.")

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login_view')
        else:
            messages.error(request, "Please correct the errors.")
    else:
        user_form = CustomUserCreationForm()

    return render(request, 'attendance/register.html', {'user_form': user_form})


def logout_view(request):
    logout(request)
    return redirect('login_view')

@login_required
@user_passes_test(is_student)
@csrf_exempt
@require_POST
def mark_attendance(request):
    try:
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

        marked_names, already_marked_names, unrecognized_face = [], [], 0

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

        if marked_names:
            return JsonResponse({"message": f"Attendance marked for: {', '.join(marked_names)} ✅"})
        elif already_marked_names:
            return JsonResponse({"message": f"Already marked: {', '.join(already_marked_names)} "})
        elif unrecognized_face > 0:
            return JsonResponse({"message": "No recognized face found ❌"})
        else:
            return JsonResponse({"message": "unknown error ❗"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    if form.is_valid():
        form.save()
        return redirect('manage_students')
    return render(request, 'attendance/student_form.html', {'form': form, 'action': 'Edit'})


@login_required
@user_passes_test(is_admin)
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect('manage_students')


# ✅ NEW: Manage admin approval
@login_required
@user_passes_test(is_admin)
def manage_admin_requests(request):
    pending_admins = Profile.objects.filter(role='admin', is_approved=False)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        profile = get_object_or_404(Profile, user__id=user_id)

        if action == 'approve':
            profile.is_approved = True
            profile.save()
            messages.success(request, f"{profile.user.username} approved as admin ✅")
        elif action == 'reject':
            profile.user.delete()
            messages.warning(request, "Admin request rejected ❌")

        return redirect('manage_admin_requests')

    return render(request, 'attendance/manage_admin_requests.html', {
        'pending_admins': pending_admins
    })
