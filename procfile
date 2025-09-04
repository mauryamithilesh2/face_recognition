
web: gunicorn face_attendance.wsgi --log-file - 
#or works good with external database
web: python manage.py migrate && gunicorn face_attendance.wsgi

