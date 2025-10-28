import os
import cv2
from .models import Student

def get_encode_faces():
    encode = {}
    students = Student.objects.all()

    for student in students:
        try:
            if not student.image:
                print(f"[✘] No image for student ID: {student.id}")
                continue

            path = student.image.path
            if not os.path.exists(path):
                print(f"[✘] Image file not found: {student.user.username}")
                continue

            image_bgr = cv2.imread(path)
            if image_bgr is None:
                print(f"[✘] Failed to read image: {student.user.username}")
                continue

            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
            if len(faces) == 0:
                print(f"[✘] No detectable face in image: {student.user.username}")
                continue
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200), interpolation=cv2.INTER_CUBIC)

            name = student.user.username
            encode[name] = face_roi
            print(f"[✔] Face prepared for: {name}")

        except Exception as e:
            print(f"[!!] Error processing {student.user.username}: {e}")

    return encode

