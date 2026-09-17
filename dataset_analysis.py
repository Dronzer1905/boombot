import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import shutil
from sklearn.model_selection import train_test_split
from collections import Counter

DATASET_DIR = "dataset"
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
TEST_DIR = os.path.join(DATASET_DIR, "test")
VAL_DIR = os.path.join(DATASET_DIR, "val")
NEW_TRAIN_DIR = os.path.join(DATASET_DIR, "new_train")

RESULTS_DIR = "results"
GRAPHS_DIR = os.path.join(RESULTS_DIR, "graphs")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")

def inspect_dataset():
    classes = sorted(os.listdir(TRAIN_DIR))
    train_counts = {}
    test_counts = {}
    
    total_train = 0
    total_test = 0
    
    image_shape = None
    channels = None
    is_grayscale = True
    
    corrupted = 0
    
    for c in classes:
        train_path = os.path.join(TRAIN_DIR, c)
        test_path = os.path.join(TEST_DIR, c)
        
        if not os.path.isdir(train_path):
            continue
            
        train_imgs = os.listdir(train_path)
        test_imgs = os.listdir(test_path)
        
        train_counts[c] = len(train_imgs)
        test_counts[c] = len(test_imgs)
        
        total_train += len(train_imgs)
        total_test += len(test_imgs)
        
        # Check an image for shape and channels
        if len(train_imgs) > 0 and image_shape is None:
            img_path = os.path.join(train_path, train_imgs[0])
            img_unchanged = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if img_unchanged is None:
                corrupted += 1
            else:
                image_shape = img_unchanged.shape[:2]
                channels = 1 if len(img_unchanged.shape) == 2 else img_unchanged.shape[2]
                if channels == 3:
                    # check if R==G==B
                    b, g, r = cv2.split(img_unchanged)
                    if not (np.array_equal(b, g) and np.array_equal(g, r)):
                        is_grayscale = False
    
    # Save graph
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(classes))
    width = 0.35
    
    train_vals = [train_counts[c] for c in classes]
    test_vals = [test_counts[c] for c in classes]
    
    ax.bar(x - width/2, train_vals, width, label='Train')
    ax.bar(x + width/2, test_vals, width, label='Test')
    ax.set_ylabel('Number of Images')
    ax.set_title('Class Distribution in FER Dataset')
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "class_distribution.png"))
    plt.close()
    
    report = f"""Dataset Analysis Report
=======================
Total Classes: {len(classes)}
Class Names: {classes}

Total Images: {total_train + total_test}
Original Train Images: {total_train}
Original Test Images: {total_test}

Image Dimensions: {image_shape[0]}x{image_shape[1]}
Image Channels (Source File): {channels}
Is Truly Grayscale: {is_grayscale}
Corrupted Images Found: {corrupted}

Class Imbalance (Train set):
"""
    for c in classes:
        report += f"  - {c}: {train_counts[c]} ({train_counts[c]/total_train*100:.2f}%)\n"
        
    print(report)
    with open(os.path.join(REPORTS_DIR, "dataset_analysis.txt"), "w") as f:
        f.write(report)
        
    return classes, is_grayscale

def create_val_split():
    # Split train into new_train and val (80/20)
    # Stratified split using fixed random seed (42)
    print("Creating Train/Validation Split (80/20) from Original Train...")
    
    os.makedirs(NEW_TRAIN_DIR, exist_ok=True)
    os.makedirs(VAL_DIR, exist_ok=True)
    
    classes = sorted(os.listdir(TRAIN_DIR))
    
    for c in classes:
        os.makedirs(os.path.join(NEW_TRAIN_DIR, c), exist_ok=True)
        os.makedirs(os.path.join(VAL_DIR, c), exist_ok=True)
        
        img_names = os.listdir(os.path.join(TRAIN_DIR, c))
        img_paths = [os.path.join(TRAIN_DIR, c, name) for name in img_names]
        
        train_imgs, val_imgs = train_test_split(img_paths, test_size=0.2, random_state=42, stratify=[c]*len(img_paths))
        
        for p in train_imgs:
            shutil.copy(p, os.path.join(NEW_TRAIN_DIR, c, os.path.basename(p)))
        for p in val_imgs:
            shutil.copy(p, os.path.join(VAL_DIR, c, os.path.basename(p)))
            
    print("Split complete.")
    print("Validation set created successfully and Original Test set untouched.")

def preprocessing_experiment(is_grayscale):
    print("Running Preprocessing Experiment...")
    classes = sorted(os.listdir(TRAIN_DIR))
    
    # take one sample image
    sample_img_path = os.path.join(TRAIN_DIR, classes[0], os.listdir(os.path.join(TRAIN_DIR, classes[0]))[0])
    
    original = cv2.imread(sample_img_path, cv2.IMREAD_UNCHANGED)
    
    # if it's already 1 channel, original is grayscale
    if len(original.shape) == 2:
        gray = original
        original_disp = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
    else:
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        original_disp = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        
    # Canny Edge
    canny = cv2.Canny(gray, 100, 200)
    
    # Sobel Edge
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    sobel = cv2.magnitude(sobelx, sobely)
    sobel = np.uint8(255 * sobel / np.max(sobel))
    
    fig, axs = plt.subplots(1, 4, figsize=(16, 4))
    axs[0].imshow(original_disp)
    axs[0].set_title("Original")
    axs[0].axis('off')
    
    axs[1].imshow(gray, cmap='gray')
    axs[1].set_title("Grayscale")
    axs[1].axis('off')
    
    axs[2].imshow(canny, cmap='gray')
    axs[2].set_title("Canny Edge")
    axs[2].axis('off')
    
    axs[3].imshow(sobel, cmap='gray')
    axs[3].set_title("Sobel Edge")
    axs[3].axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "preprocessing_experiment.png"))
    plt.close()
    
    print("Preprocessing visualization saved.")

if __name__ == "__main__":
    classes, is_grayscale = inspect_dataset()
    if not os.path.exists(NEW_TRAIN_DIR):
        create_val_split()
    else:
        print("Train/Val split already exists.")
    preprocessing_experiment(is_grayscale)
