import datetime
import pickle
import face_recognition
# The library face_recognition is based on deep learning, it supports single-shot learning which means it needs a single picture to train itself to detect a person.
import os
import numpy as np
import datetime
from flask import Flask, render_template, Response,request, redirect,url_for
import cv2
from flask_socketio import SocketIO
import psycopg2
import time

app = Flask(__name__)
socketio = SocketIO(app)

conn = psycopg2.connect(
    dbname="'face_attendance_30DEC23'",
    user="odoo",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()
img_cap = cv2.VideoCapture(0)
last_frame = None

captured_frames = []
output_folder = 'training_folders/'

@app.route('/')
def index():
    return render_template('face_recognition.html')

@app.route('/registration')
def registration():
    return render_template('registration_page.html')

def capture_frame():
    success, frame = img_cap.read()
    if success:
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()
    return None


@app.route('/capture_frame')
def get_frame():
    global last_frame
    last_frame = capture_frame()
    captured_frames.append(last_frame)
    return Response(last_frame, mimetype='image/jpeg')


def generate_frames_for_image():
    while True:
        success, frame = img_cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/capture_img_feed')
def capture_img():
    return Response(generate_frames_for_image(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/save_images', methods=['POST'])
def save_images():
    name = request.form['name']
    user_id = request.form['user_id']
    folder_name = f"{name}_{user_id}"
    folder_path = os.path.join(output_folder, folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i, frame in enumerate(captured_frames):
        file_path = os.path.join(folder_path, f"image_{i}.jpg")
        with open(file_path, 'wb') as file:
            file.write(frame)

    # Clear the captured_frames list after saving
    captured_frames.clear()

    return redirect(url_for('registration'))


def broadcast_name(name, image_url, rec_date, rec_time):
    socketio.emit('update_name', {'name': name, 'image_url': image_url, 'rec_date': rec_date, 'rec_time': rec_time})


def save_to_database(employee_id, check_in, check_out, worked_hours, overtime_hours):
    query = "INSERT INTO hr_attendance (employee_id, check_in, check_out,worked_hours,overtime_hours) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (employee_id, check_in, check_out, worked_hours, overtime_hours))
    conn.commit()

last_attendance_time = {}
def markAttendance(name):
    current_time = time.time()

    if name in last_attendance_time.keys() and (current_time - last_attendance_time[name]) > 20:
        last_attendance_time[name] = current_time
        save_to_database(6, datetime.datetime.now(), None, 1.0, 1.0)
    if name not in last_attendance_time.keys():
        last_attendance_time[name] = current_time
        save_to_database(6, datetime.datetime.now(), None, 1.0, 1.0)


def generate_frames():
    path = 'Training_images'

    images = []
    classNames = []
    mylist = os.listdir(path)
    for cl in mylist:
        curImg = cv2.imread(f'{path}/{cl}')
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

    def findEncodings(images):
        encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encoded_face = face_recognition.face_encodings(img)[0]
            encodeList.append(encoded_face)
        return encodeList

    encoded_face_train = findEncodings(images)

    # take pictures from webcam
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        faces_in_frame = face_recognition.face_locations(imgS)
        encoded_faces = face_recognition.face_encodings(imgS, faces_in_frame)
        for encode_face, faceloc in zip(encoded_faces, faces_in_frame):
            matches = face_recognition.compare_faces(encoded_face_train, encode_face)
            faceDist = face_recognition.face_distance(encoded_face_train, encode_face)
            matchIndex = np.argmin(faceDist)
            matches_id = 0
            if np.any(faceDist <= 0.5):
                matches_id = matches[matchIndex]
            if matches_id:
                name = classNames[matchIndex].upper().lower()
                y1, x2, y2, x1 = faceloc
                # since we scaled down by 4 times
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 5), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 2)
                # cv2.putText(img,'abc', (x1+6,y2+15), cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                rec_date = datetime.date.today()
                rec_time = datetime.datetime.now()
                broadcast_name(name.capitalize(), f'/static/img/{name.capitalize()}.jpg', rec_date.strftime('%d-%m-%Y'),
                               rec_time.strftime('%H:%M:%S'))
                markAttendance(name)
            else:
                name = 'Unknown'
                y1, x2, y2, x1 = faceloc
                # since we scaled down by 4 times
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 0, 255), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 5), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 2)
                # cv2.putText(img, 'abc', (x1 + 6, y2 + 15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                # markAttendance(name)

        # success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    #


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True, host="0.0.0.0", port="5024")

#
