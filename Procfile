web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn face_attendance.wsgi:application --bind 0.0.0.0:$PORT --log-file -
