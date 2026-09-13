import cv2
import numpy as np
from tensorflow.keras.models import load_model
from flask import Flask, render_template_string, Response

# Initialize Flask App
app = Flask(__name__)

# Load emotion model
model = load_model("emotion_detection_model.h5")

# Face detector
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Emotion labels
emotions = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

# Initialize camera
cap = cv2.VideoCapture(0)

def generate_frames():
    """Generator function that continuously reads from the camera, processes, and yields frames."""
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, (48, 48))
                face = face / 255.0
                face = np.reshape(face, (1, 48, 48, 1))

                # Make prediction
                pred = model.predict(face, verbose=0) # verbose=0 hides console spam on RPi
                emotion = emotions[np.argmax(pred)]

                # Draw rectangle and label
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, emotion, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in the multipart/x-mixed-replace format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# HTML template embedded as a string for simplicity
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPi Emotion Detection</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #1e1e1e; color: #fff; padding: 20px; }
        .video-container { margin-top: 20px; border: 4px solid #4CAF50; display: inline-block; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        img { display: block; max-width: 100%; height: auto; }
    </style>
</head>
<body>
    <h1>Raspberry Pi Emotion Detection Stream</h1>
    <div class="video-container">
        <!-- This image tag calls the /video_feed route to get the MJPEG stream -->
        <img src="{{ url_for('video_feed') }}" alt="Video Stream">
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Route to render the main HTML page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Route to handle the MJPEG stream."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # Ensure Flask is installed: pip install flask
    # host='0.0.0.0' allows external devices on the same network to access the stream
    app.run(host='0.0.0.0', port=5000, debug=False)