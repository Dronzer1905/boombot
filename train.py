import os
import torch
from ultralytics import YOLO

def main():
    # 1. Verify CUDA / RTX 4060 is available
    print("--- GPU Check ---")
    if torch.cuda.is_available():
        print(f"CUDA is available! GPU detected: {torch.cuda.get_device_name(0)}")
    else:
        print("WARNING: CUDA is not available. Training will fall back to CPU and be very slow.")
        print("Please ensure you have installed the CUDA-enabled version of PyTorch.")
        return

    # 2. Set Local Dataset Path
    # Make sure this points to your actual dataset folder path!
    yaml_path = "Facial Emotion Detection.v1i.yolov11/data.yaml"

    if not os.path.exists(yaml_path):
        print(f"\nERROR: Could not find data.yaml at {yaml_path}")
        print("Please update the 'yaml_path' variable with the correct location.")
        return

    print(f"\nUsing local dataset at: {yaml_path}")

    # 3. Initialize YOLOv11 Nano Model
    print("\n--- Initializing YOLOv11 Nano ---")
    model = YOLO('yolo11n.pt') 

    # 4. Train the Model (Memory Optimized & RPi Tuned)
    print("\n--- Starting Training ---")
    results = model.train(
        data=yaml_path,        
        epochs=50,             
        imgsz=416,             # TUNED FOR RPI: Reduced from 640 to 416 for much faster inference on Pi
        batch=16,              
        device=0,              
        workers=4,             
        amp=True,              
        project="Emotion_Model", 
        name="yolo11n_run1",   
        patience=15,           
        save=True              
    )

    print("\n--- Training Complete ---")
    print(f"Your trained model weights are saved in: Emotion_Model/yolo11n_run1/weights/best.pt")

    # 5. Export for Raspberry Pi (ARM CPU Optimization)
    print("\n--- Exporting Model for Raspberry Pi ---")
    # Load the best trained model
    best_model = YOLO("Emotion_Model/yolo11n_run1/weights/best.pt")
    
    # Export to NCNN format (Highly optimized for Raspberry Pi ARM CPUs)
    print("Exporting to NCNN format... This may take a few minutes.")
    best_model.export(format="ncnn", imgsz=416)
    
    print("\nDone! To use on your RPi, copy the entire 'Emotion_Model/yolo11n_run1/weights/best_ncnn_model' folder to the Pi.")

if __name__ == '__main__':
    # Required for Windows multi-processing
    main()