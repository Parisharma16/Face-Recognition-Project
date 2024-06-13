  
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

# Add your own Firebase config details
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
import cv2
import numpy as np
from datetime import datetime
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
                    # Get the Data
                    studentInfo = db.child('Students').child(f'{names[id]}1').get()
                    studentdata = studentInfo.val()

                    print('this is data', studentInfo.val())
                    # Get the Image from the storage
                    blob = bucket.get_blob(f'Images/{names[id]}.jpeg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    # Update data of attendance
                    datetimeObject = datetime.strptime(studentdata['Last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)

                    if db.child('Students').child(f'{names[id]}1').child('Status') == "IN":
                        
                        db.child('Students').child(f'{names[id]}1').child("Status").update("OUT")
                       
                    if db.child('Students').child(f'{names[id]}1').child('Status') == "OUT":
                       
                        db.child('Students').child(f'{names[id]}1').child("Status").update("IN")
                       

                    if secondsElapsed > 10:
                        ref = db.child('Students').child(f'{names[id]}1')
                        studentdata['Total_attendance'] += 1
                        ref.child('Total_attendance').set(studentdata['Total_attendance'])

                        print('Seconds are more than 10')

                        ref.child('Status').set('OUT')
                    else:
                        counter = 0
                    ref.child('Last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            cv2.putText(frame, str(names[id]), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
            cv2.putText(frame, str(confidence), (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# Define the route for the login page
@app.route("/signin")
def login():
    return render_template("login.html")


# Define the route for the signup page
@app.route("/")
def signup():
    return render_template("signup.html")


# Define the route for the welcome page
import base64


@app.route("/welcome")
def welcome():
    if person["is_logged_in"]:
        if person["name"] != 'none':
            studentInfo = db.child('Students').child(person["name"] + '1').get()
            studentdata = studentInfo.val()
            if studentdata is None:
                return render_template("welcome.html", email=person["email"], name="Sakshi", img=None, status="OUT")
            
            blob = bucket.get_blob(f'Images/{person["name"]}.jpeg')
            if blob is None:
                return render_template("welcome.html", email=person["email"], name="Sakshi", img=None, status="OUT")
            
            array = np.frombuffer(blob.download_as_bytes(), np.uint8)
            img_encoded = base64.b64encode(array).decode('utf-8')
            
            db.child('Students').child(person["name"] + '1').child('Status').set('IN')
            datetimeObject = datetime.strptime(studentdata['Last_attendance_time'], "%Y-%m-%d %H:%M:%S")
            secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
            if secondsElapsed > 10:
                ref = db.child('Students').child(person["name"] + '1')
                studentdata['Total_attendance'] += 1
                ref.child('Total_attendance').set(studentdata['Total_attendance'])
                ref.child(person["name"] + '1').child('Status').set('OUT')
            ref.child('Last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return render_template("welcome.html", email=person["email"], name="Sakshi", img=img_encoded, status=studentdata["Status"])
        else:
            return render_template("welcome.html", email=person["email"], name="Sakshi", img=None, status="OUT")
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
            newdata = {"Name":person["name"],"Major":"","Starting_year":0,"Total_attendance":0,"Last_attendance_time":"","Status":"NA"}
            db.child("Students").child(person["name"]).set(newdata)
            
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
