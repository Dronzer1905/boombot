import os
import cv2
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

class FERDataset(Dataset):
    def __init__(self, data_dir, classes, transform=None, mode='baseline', edge_type='sobel'):
        """
        mode: 'baseline' (original gray), 'edge' (only edges), 'fusion' (returns both)
        """
        self.data_dir = data_dir
        self.classes = classes
        self.transform = transform
        self.mode = mode
        self.edge_type = edge_type
        
        self.image_paths = []
        self.labels = []
        
        for idx, c in enumerate(self.classes):
            class_dir = os.path.join(data_dir, c)
            if os.path.isdir(class_dir):
                for img_name in os.listdir(class_dir):
                    self.image_paths.append(os.path.join(class_dir, img_name))
                    self.labels.append(idx)
                    
    def __len__(self):
        return len(self.image_paths)
        
    def _get_edges(self, gray_img):
        if self.edge_type == 'sobel':
            sobelx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
            sobel = cv2.magnitude(sobelx, sobely)
            sobel = np.uint8(255 * sobel / np.max(sobel)) if np.max(sobel) > 0 else np.uint8(sobel)
            return sobel
        elif self.edge_type == 'canny':
            return cv2.Canny(gray_img, 100, 200)
        return gray_img

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # Read as grayscale
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        if self.mode == 'baseline':
            img = gray
        elif self.mode == 'edge':
            img = self._get_edges(gray)
        elif self.mode == 'fusion':
            orig = gray
            edge = self._get_edges(gray)
        
        if self.mode in ['baseline', 'edge']:
            # Convert to PIL Image for torchvision transforms
            img = transforms.functional.to_pil_image(img)
            if self.transform:
                img = self.transform(img)
            return img, label
            
        elif self.mode == 'fusion':
            orig = transforms.functional.to_pil_image(orig)
            edge = transforms.functional.to_pil_image(edge)
            
            # For fusion, if we apply random spatial transforms (like flip/rotation), 
            # we MUST apply the exact same transform to both branches.
            # To do this safely, we can stack them, transform, then split.
            # However, for simplicity and correctness in torchvision, we will apply seed matching or functional transforms.
            
            if self.transform:
                # Apply same transform to both using functional API if needed, 
                # or just use random seed matching. 
                # A robust way is to concatenate as a 2-channel image, transform, then split.
                # Here we just apply basic deterministic transforms for validation/test.
                # For training with augmentations, we should use a custom transform approach.
                pass
            
            # Manual basic transforms for now
            orig = transforms.functional.to_tensor(orig)
            edge = transforms.functional.to_tensor(edge)
            
            # Simple normalization
            orig = transforms.functional.normalize(orig, [0.5], [0.5])
            edge = transforms.functional.normalize(edge, [0.5], [0.5])
            
            return orig, edge, label

def get_dataloaders(train_dir, val_dir, test_dir, batch_size=64, mode='baseline'):
    classes = sorted(os.listdir(train_dir))
    
    # Phase 7 - Data Augmentation (Only on Train)
    # Updated transforms for 64x64 input and richer augmentations
    train_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.RandomApply([transforms.GaussianBlur(kernel_size=(3,3), sigma=(0.1,2.0))], p=0.3),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    
    val_test_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    
    # Custom handling for fusion mode transformations to ensure spatial consistency
    if mode == 'fusion':
        train_dataset = FusionDataset(train_dir, classes, transform=True, mode=mode)
        val_dataset = FusionDataset(val_dir, classes, transform=False, mode=mode)
        test_dataset = FusionDataset(test_dir, classes, transform=False, mode=mode)
    else:
        train_dataset = FERDataset(train_dir, classes, transform=train_transform, mode=mode)
        val_dataset = FERDataset(val_dir, classes, transform=val_test_transform, mode=mode)
        test_dataset = FERDataset(test_dir, classes, transform=val_test_transform, mode=mode)
        
    # Phase 8 - Class Imbalance Weights
    class_counts = [0] * len(classes)
    for c_idx, c in enumerate(classes):
        class_counts[c_idx] = len(os.listdir(os.path.join(train_dir, c)))
        
    total_samples = sum(class_counts)
    class_weights = [total_samples / (len(classes) * count) for count in class_counts]
    class_weights_tensor = torch.FloatTensor(class_weights)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    
    return train_loader, val_loader, test_loader, class_weights_tensor, classes

# To handle fusion augmentation synchronously:
class FusionDataset(FERDataset):
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        edge = self._get_edges(gray)
        
        orig_pil = transforms.functional.to_pil_image(gray)
        edge_pil = transforms.functional.to_pil_image(edge)
        
        if self.transform: # Training mode
            # Apply identical random transforms to both
            if torch.rand(1).item() > 0.5:
                orig_pil = transforms.functional.hflip(orig_pil)
                edge_pil = transforms.functional.hflip(edge_pil)
                
            angle = transforms.RandomRotation.get_params([-10, 10])
            orig_pil = transforms.functional.rotate(orig_pil, angle)
            edge_pil = transforms.functional.rotate(edge_pil, angle)
            
            translations = transforms.RandomAffine.get_params(degrees=[0,0], translate=[0.1, 0.1], scale_ranges=None, shears=None, img_size=[48, 48])
            orig_pil = transforms.functional.affine(orig_pil, *translations)
            edge_pil = transforms.functional.affine(edge_pil, *translations)
            
        orig_tensor = transforms.functional.to_tensor(orig_pil)
        edge_tensor = transforms.functional.to_tensor(edge_pil)
        
        orig_tensor = transforms.functional.normalize(orig_tensor, [0.5], [0.5])
        edge_tensor = transforms.functional.normalize(edge_tensor, [0.5], [0.5])
        
        return orig_tensor, edge_tensor, label
