from flask import Flask, request, jsonify,Response
from flask_cors import CORS
import cv2
app = Flask(__name__)
CORS(app)
video=cv2.VideoCapture(1)

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    """Generate frame by frame from camera."""
    while True:
        success, frame = video.read()  # Read the camera frame
        if not success:
            break
        else:
            # Process the frame as needed (e.g., detect faces)
            # Example processing: convert frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Encode the processed frame into JPEG format
            ret, buffer = cv2.imencode('.jpg', gray_frame)
            if not ret:
                break
            # Convert the frame into bytes
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/', methods=['POST'])
def detect_faces():

    try:
        data = request.json
        if 'text' not in data:
            print('No text data provided')
            return jsonify({'error': 'No text data provided'})
        text = data['text']
        return 'hii'
    except Exception as e:
        print('err')
        return jsonify({'error': str(e)})


@app.route('/data')
def get_time():
    return {
        'Name':"geek", 
        "Age":"22",
        "programming":"python"
        }


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=True)
