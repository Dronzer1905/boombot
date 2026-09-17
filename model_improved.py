import torch
import torch.nn as nn
import torch.nn.functional as F

class ImprovedBaselineCNN(nn.Module):
    """A slightly deeper CNN (still lightweight) for 64x64 grayscale input.
    Parameters kept < 1M so it fits on Raspberry Pi 5.
    """
    def __init__(self, num_classes=7):
        super(ImprovedBaselineCNN, self).__init__()
        # Input 1x64x64
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.conv5 = nn.Conv2d(256, 512, kernel_size=3, padding=1)
        self.bn5 = nn.BatchNorm2d(512)
        self.pool = nn.MaxPool2d(2, 2)  # halves size each time
        self.dropout = nn.Dropout(0.4)
        # After 5 pools: 64 -> 32 -> 16 -> 8 -> 4 -> 2
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(512, num_classes)
        
    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.pool(F.relu(self.bn4(self.conv4(x))))
        x = self.pool(F.relu(self.bn5(self.conv5(x))))
        x = self.gap(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.fc(x)
        return x

# Keep the existing EdgeFusionCNN (unchanged) for reference
from model import EdgeFusionCNN
