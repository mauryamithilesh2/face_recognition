import cv2
import numpy as np
from .models import Student


def _load_face_roi(image_bgr):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = gray[y : y + h, x : x + w]
    face = cv2.resize(face, (200, 200), interpolation=cv2.INTER_CUBIC)
    return face


def get_encode_faces(user=None):
    """
    Returns face ROIs (200x200 grayscale) keyed by username for LBPH training.
    If `user` is provided, only returns that user's face ROI.
    """
    known_faces = {}

    def load_student_face(student, key):
        if not student.image:
            return
        try:
            img_path = student.image.path
            image_bgr = cv2.imread(img_path)
            if image_bgr is None:
                return
            face = _load_face_roi(image_bgr)
            if face is not None:
                known_faces[key] = face
        except Exception as e:
            print(f"[ERROR] Could not prepare face for {key}: {e}")

    if user:
        try:
            student = Student.objects.get(user=user)
            load_student_face(student, user.username)
        except Student.DoesNotExist:
            pass
    else:
        for student in Student.objects.all():
            load_student_face(student, student.user.username)

    return known_faces
