import os
import glob
from ultralytics import YOLO

def main():
    print("--- Exporting Specific Trained Model ---")
    # Explicitly point to yolo11n_run12
    model_path = "runs/detect/Emotion_Model/yolo11n_run12/weights/best.pt"
    
    if not os.path.exists(model_path):
        print(f"ERROR: Could not find the model at {model_path}")
        return

    print(f"Found your successfully trained model at: {model_path}")
    
    print("\n--- Exporting Model for Raspberry Pi ---")
    print("Loading model...")
    best_model = YOLO(model_path)
    
    print("Exporting to NCNN format... This may take a few minutes.")
    best_model.export(format="ncnn", imgsz=416)
    
    print(f"\nSuccess! The export is complete.")
    print("Look inside the folder where your best.pt is located to find the new 'best_ncnn_model' folder.")
    print("Copy that entire 'best_ncnn_model' folder to your Raspberry Pi.")

if __name__ == '__main__':
    main()