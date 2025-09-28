from django.urls import path
# from django.contrib.auth.views import LogoutView

from . import views

urlpatterns =[
    path('', views.home, name='home'),
    path('register/', views.register, name='register'), 
    path('login/',views.login_view,name='login_view'),
    path('logout/',views.logout_view,name='logout_view'),
    
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),

    path('mark/',views.mark_attendance,name = 'mark_attendance'),
    # path('student_attendance/', views.student_attendance, name='student_attendance'),
    path('teacher_attendance/', views.teacher_attendance_view, name='teacher_all_attendance'),
    path('admin_attendance/', views.admin_attendance_view, name='admin_attendance'),
    path('manage_teachers/', views.manage_teachers, name='manage_teachers'),

    #student management 
    path('manage_students/', views.manage_students, name='manage_students'),
    path('add_student/',views.add_student,name='add_student'),
    path('edit_student/<int:student_id>/',views.edit_student,name='edit_student'),

    path('delete_student/<int:student_id>/',views.delete_student,name='delete_student'),

    # alias for templates expecting 'student_attendance'
    path('student_attendance/', views.student_dashboard, name='student_attendance'),
]