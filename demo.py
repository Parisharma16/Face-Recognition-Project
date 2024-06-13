import face_recognition
import cv2
import os

# Path to the directory containing known faces
KNOWN_FACES_DIR = 'known_faces'

# Load known faces and labels from the 'known_faces' directory
known_faces_encodings = []
known_faces_labels = []

for person_name in os.listdir(KNOWN_FACES_DIR):
    person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue  # Skip if not a directory
    for filename in os.listdir(person_dir):
        image_path = os.path.join(person_dir, filename)
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) > 0:
            face_location = face_locations[0]  # Get the location of the top face
            face_encodings = face_recognition.face_encodings(image, [face_location])
            known_faces_encodings.extend(face_encodings)
            known_faces_labels.extend([person_name] * len(face_encodings))  # Repeat label for each encoding

TOLERANCE = 0.4
# Initialize the webcam
video_capture = cv2.VideoCapture(0)

while True:
    # Capture each frame from the webcam
    ret, frame = video_capture.read()

    # Convert the frame from BGR to RGB (required by face_recognition library)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find all the faces in the current frame
    face_locations = face_recognition.face_locations(rgb_frame)
    if len(face_locations) > 0:
        face_location = face_locations[0]  # Get the location of the top face
        face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare the current face encoding with the known faces
            results = face_recognition.compare_faces(known_faces_encodings, face_encoding, TOLERANCE)
            match = "Unknown"

            # Check if there is a match
            if True in results:
                match = known_faces_labels[results.index(True)]

            # Display the name of the recognized face on the frame
            top_left = (face_location[3], face_location[0])
            bottom_right = (face_location[1], face_location[2])
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(frame, match, (face_location[3] + 6, face_location[2] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the frame
    cv2.imshow('Video', frame)

    # Check for the 'q' key to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close all OpenCV windows
video_capture.release()
cv2.destroyAllWindows()