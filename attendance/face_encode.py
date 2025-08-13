import os
import face_recognition
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

            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)

            if encoding:
                name = student.user.username  # ✅ Use consistent unique name
                encode[name] = encoding[0]
                print(f"[✔] Face encoded for: {name}")
            else:
                print(f"[✘] No detectable face in image: {student.user.username}")

        except Exception as e:
            print(f"[!!] Error processing {student.user.username}: {e}")

    return encode

