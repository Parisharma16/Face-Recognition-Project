import pyrebase
from flask import Flask, render_template, redirect, url_for, request, Response
import cv2
import os
import firebase_admin
from firebase_admin import initialize_app
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
import numpy as np

app = Flask(__name__)
video = cv2.VideoCapture(1)

cred = credentials.Certificate('serviceAccountkey.json')


config = {
    "apiKey": "AIzaSyDjX8Vi_sMFhoaaPsV2G1QHlMVBt5RRTnY",
    "authDomain": "libraryentryrealtime.firebaseapp.com",
    "databaseURL": "https://libraryentryrealtime-default-rtdb.firebaseio.com",
    "projectId": "libraryentryrealtime",
    "storageBucket": "libraryentryrealtime.appspot.com",
    "messagingSenderId": "793845980290",
    "appId": "1:793845980290:web:7d4c7a672add90dcb5e89b",
    "measurementId": "G-52BPTVGV81"
};




# Initialize Firebase
firebase = pyrebase.initialize_app(config)
firebase_admin.initialize_app(cred,config)
auth = firebase.auth()
db = firebase.database()
bucket = storage.bucket()

# Initialize person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}



recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

font = cv2.FONT_HERSHEY_SIMPLEX


# Define the route for video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# print("hi, generate frame about to begin")
# Define the function to generate video frames

import time
def generate_frames():
    # initiate id counter
    id = 0

    # names related to ids: example ==> Marcelo: id=1,  etc
    names = ['None', 'Sakshi', 'Pari']
    # Initialize and start realtime video capture
    cam = cv2.VideoCapture(0)
    cam.set(3, 640)  # set video width
    cam.set(4, 480)  # set video height

    # Define min window size to be recognized as a face
    minW = 0.1 * cam.get(3)
    minH = 0.1 * cam.get(4)
    counter = 0
    last_status_update_time = time.time()

    while True:
        ret, frame = cam.read()
        frame = cv2.flip(frame, -1)  # Flip vertically
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH))
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            if confidence < 100 and counter == 0:
                name = names[id]
                confidence = "  {0}%".format(round(100 - confidence))
                counter = 1
            else:
                name = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))

            if counter != 0:
                if counter == 1:

                    studentInfo = db.child('Students').child(f'{names[id]}1').get()
                    student = db.child('Students').child(f'{names[id]}1').get()
                    studentdata = studentInfo.val()
                    print(studentdata)

                    blob = bucket.get_blob(f'Images/{names[id]}.jpeg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    current_time = time.time()
                    #print(current_time)
                    seconds_elapsed = current_time - last_status_update_time
                    print("the time elapsed is", seconds_elapsed)

                    #db.child('Students').child(f'{names[id]}1').update({'Status': 'IN'})
                    current_status = db.child('Students').child(f'{names[id]}1').child('Status').get().val()
                    print(current_status)

                    if seconds_elapsed > 15:
                        if current_status == 'IN':
                            db.child('Students').child(f'{names[id]}1').update({'Status': 'OUT'})
                            print("yes")
                            last_status_update_time = current_time  # Update only when the status changes
                        elif current_status == 'OUT':
                            db.child('Students').child(f'{names[id]}1').update({'Status': 'IN'})
                            #print("here")
                            last_status_update_time = current_time  # Update only when the status changes
                        #print("second_elapsed", seconds_elapsed)

                    
                    else:
                        #student.update(f{'Status':{current_status}})
                        db.child('Students').child(f'{names[id]}1').update({'Status': current_status})
                        #student.update({'Status': current_status})


            cv2.putText(frame, str(names[id]), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
            cv2.putText(frame, str(confidence), (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Define the route for the login page
@app.route("/")
def login():
    return render_template("login.html")


# Define the route for the signup page
@app.route("/signup")
def signup():
    return render_template("signup.html")


# Define the route for the welcome page
@app.route("/welcome")
def welcome():
    if person["is_logged_in"]:
        return render_template("welcome.html", email=person["email"], name=person["name"])
    else:
        return redirect(url_for('login'))


# Define the route for handling login
@app.route("/result", methods=["POST", "GET"])
def result():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            data = db.child("users").get()
            person["name"] = data.val()[person["uid"]]["name"]
            return redirect(url_for('welcome'))
        except:
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"]:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))


# Define the route for handling registration
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        try:
            auth.create_user_with_email_and_password(email, password)
            user = auth.sign_in_with_email_and_password(email, password)
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            data = {"name": name, "email": email}
            db.child("users").child(person["uid"]).set(data)
            return redirect(url_for('welcome'))
        except:
            return redirect(url_for('register'))
    else:
        if person["is_logged_in"]:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('register'))


if __name__ == "__main__":
    app.run(debug=True)
