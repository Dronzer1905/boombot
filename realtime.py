# src/real_time_inference.py
import cv2
import torch
import numpy as np
from torchvision import transforms
from model_improved import ImprovedBaselineCNN
import json
import os

# -------------------------------------------------
# Helper: load model & config
# -------------------------------------------------
def load_model():
    cfg_path = os.path.join('models', 'model_config.json')
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

    # model expects 64×64 grayscale, 7 classes
    model = ImprovedBaselineCNN(num_classes=len(cfg['classes']))
    model_path = os.path.join('models', 'best_emotion_model.pth')
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model, cfg['classes']

# -------------------------------------------------
# Pre‑processing: face detection → 64×64 gray tensor
# -------------------------------------------------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def preprocess_frame(frame):
    """Detect the biggest face, convert to gray, resize, normalize."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return None  # no face found

    # pick the largest face
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
    face_crop = gray[y:y+h, x:x+w]

    pil_img = transforms.functional.to_pil_image(face_crop)
    tensor = transform(pil_img)               # shape: (1, 64, 64)
    return tensor.unsqueeze(0)                # add batch dim → (1, 1, 64, 64)

# -------------------------------------------------
# Inference wrapper
# -------------------------------------------------
def predict(model, tensor):
    with torch.no_grad():
        logits = model(tensor)                # (1, 7)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        pred_idx = int(np.argmax(probs))
    return pred_idx, probs[pred_idx], probs

# -------------------------------------------------
# Main loop – press ‘q’ to quit
# -------------------------------------------------
def main():
    model, class_names = load_model()
    cap = cv2.VideoCapture(0)   # default webcam; change index if needed

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        tensor = preprocess_frame(frame)
        if tensor is not None:
            idx, confidence, probs = predict(model, tensor)
            label = class_names[idx]
            # overlay result
            cv2.putText(frame, f"{label} ({confidence:.2f})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "No face detected",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow('Emotion Inference', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()