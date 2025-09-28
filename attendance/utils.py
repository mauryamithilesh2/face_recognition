# utils.py

import face_recognition
import numpy as np
from .models import Student

def get_encode_faces(user=None):
    """
    Returns face encodings.
    - If `user` is provided → only returns encoding for that user.
    - If `user` is None → returns all student encodings.
    """
    known_faces = {}

    if user:
        # ✅ Only one student
        try:
            student = Student.objects.get(user=user)
            if student.image:
                img_path = student.image.path
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_faces[user.username] = encodings[0]
        except Student.DoesNotExist:
            pass
    else:
        # 🔄 Fallback: load all students
        students = Student.objects.all()
        for student in students:
            if not student.image:
                continue
            try:
                img_path = student.image.path
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_faces[student.user.username] = encodings[0]
            except Exception as e:
                print(f"[ERROR] Could not encode face for {student.user.username}: {e}")
                continue

    return known_faces
