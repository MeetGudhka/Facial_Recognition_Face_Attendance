import base64
import numpy as np
import cv2
import face_recognition
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from datetime import datetime
import json
from django.shortcuts import render

@csrf_exempt
def start_attendance(request):
    if request.method != 'POST':
        return HttpResponse("Only POST allowed", status=405)

    try:
        data = json.loads(request.body)
        image_data = data.get('image')

        if not image_data:
            return HttpResponse("No image data", status=400)

        # Decode base64 image
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return HttpResponse("Image could not be decoded", status=400)

        # Load known faces
        known_faces_dir = os.path.join(settings.BASE_DIR, 'attendance', 'known_faces')
        known_encodings = []
        known_names = []

        for filename in os.listdir(known_faces_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(known_faces_dir, filename)
                img = cv2.imread(path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(img_rgb)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(os.path.splitext(filename)[0])

        # Encode uploaded frame
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb_small_frame)
        if not encodings:
            return HttpResponse("No face detected")

        matched_name = None
        for encode_face in encodings:
            matches = face_recognition.compare_faces(known_encodings, encode_face)
            face_dis = face_recognition.face_distance(known_encodings, encode_face)

            if matches and min(face_dis) < 0.5:
                match_index = np.argmin(face_dis)
                matched_name = known_names[match_index]
                break

        if matched_name:
            # Write to Attendance.csv
            attendance_path = os.path.join(settings.BASE_DIR, 'attendance', 'Attendance.csv')
            os.makedirs(os.path.dirname(attendance_path), exist_ok=True)
            if not os.path.exists(attendance_path):
                with open(attendance_path, 'w') as f:
                    f.write('Name,Time\n')

            with open(attendance_path, 'r+') as f:
                lines = f.readlines()
                names_logged = [line.split(',')[0] for line in lines]
                if matched_name not in names_logged:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f'{matched_name},{now}\n')

            return HttpResponse(f"{matched_name} marked present.")
        else:
            return HttpResponse("Face not recognized.")

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

def index(request):
    return render(request, 'attendance/index.html')


import csv

def view_attendance(request):
    attendance_file = os.path.join(settings.BASE_DIR, 'attendance', 'Attendance.csv')
    data = []

    if os.path.exists(attendance_file):
        with open(attendance_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

    return render(request, 'attendance/view_attendance.html', {'data': data})
