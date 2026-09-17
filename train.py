import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, WeightedRandomSampler

# Local imports
from model_improved import ImprovedBaselineCNN
from model import EdgeFusionCNN
from dataset import get_dataloaders

class FocalLoss(nn.Module):
    """Focal loss with optional class weighting (gamma=2.0)."""
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor = None):
        super().__init__()
        self.gamma = gamma
        self.weight = weight
        self.ce = nn.CrossEntropyLoss(weight=weight, reduction='none')

    def forward(self, logits, target):
        # logits: (B, C), target: (B,)
        ce_loss = self.ce(logits, target)
        pt = torch.exp(-ce_loss)
        focal = ((1 - pt) ** self.gamma) * ce_loss
        return focal.mean()

def train_one_model(model, model_name, train_loader, val_loader, criterion, optimizer, scheduler, num_epochs, device):
    best_val_loss = float('inf')
    best_epoch = 0
    patience = 8
    patience_counter = 0
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    model_path = os.path.join('models', f"{model_name}.pth")

    for epoch in range(num_epochs):
        # ---------- Training ----------
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for batch in train_loader:
            if model_name == 'fusion':
                img, edge, labels = batch[0].to(device), batch[1].to(device), batch[2].to(device)
                outputs = model(img, edge)
                batch_sz = img.size(0)
            else:
                img, labels = batch[0].to(device), batch[1].to(device)
                outputs = model(img)
                batch_sz = img.size(0)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_sz
            _, pred = torch.max(outputs, 1)
            correct += (pred == labels).sum().item()
            total += batch_sz
        train_loss = running_loss / total
        train_acc = correct / total

        # ---------- Validation ----------
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for batch in val_loader:
                if model_name == 'fusion':
                    img, edge, labels = batch[0].to(device), batch[1].to(device), batch[2].to(device)
                    outputs = model(img, edge)
                    batch_sz = img.size(0)
                else:
                    img, labels = batch[0].to(device), batch[1].to(device)
                    outputs = model(img)
                    batch_sz = img.size(0)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * batch_sz
                _, pred = torch.max(outputs, 1)
                val_correct += (pred == labels).sum().item()
                val_total += batch_sz
        val_loss = val_loss / val_total
        val_acc = val_correct / val_total

        # Scheduler step (after epoch)
        scheduler.step()

        # Record history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        print(f"[{model_name}] Epoch {epoch+1}/{num_epochs} - Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch + 1
            torch.save(model.state_dict(), model_path)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered.")
                break

    print(f"Best validation loss: {best_val_loss:.4f} at epoch {best_epoch}")
    # Save history JSON
    os.makedirs('results/reports', exist_ok=True)
    with open(os.path.join('results/reports', f"{model_name}_history.json"), 'w') as f:
        json.dump(history, f)
    return history

def plot_history(history, model_name):
    epochs = range(1, len(history['train_loss']) + 1)
    # Accuracy plot
    plt.figure(figsize=(8,6))
    plt.plot(epochs, history['train_acc'], label='Train Acc')
    plt.plot(epochs, history['val_acc'], label='Val Acc')
    plt.title(f'{model_name.upper()} Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join('results/graphs', f"{model_name}_accuracy.png"))
    plt.close()
    # Loss plot
    plt.figure(figsize=(8,6))
    plt.plot(epochs, history['train_loss'], label='Train Loss')
    plt.plot(epochs, history['val_loss'], label='Val Loss')
    plt.title(f'{model_name.upper()} Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join('results/graphs', f"{model_name}_loss.png"))
    plt.close()

def main():
    device = torch.device('cpu')
    print(f"Using device: {device}")
    train_dir = os.path.join('dataset', 'new_train')
    val_dir = os.path.join('dataset', 'val')
    test_dir = os.path.join('dataset', 'test')
    num_epochs = 30  # longer training for better convergence
    batch_size = 128
    models_to_train = ['baseline', 'edge', 'fusion']
    for model_name in models_to_train:
        print('\n' + '='*30 + f"\nTraining {model_name.upper()} model\n" + '='*30)
        # Dataloaders (train, val, test, class_weights, classes)
        train_loader, val_loader, _, class_weights, classes = get_dataloaders(
            train_dir, val_dir, test_dir, batch_size=batch_size, mode=model_name)
        # WeightedRandomSampler for class imbalance
        # Convert class_weights (tensor of size C) to per‑sample weights
        sample_weights = [class_weights[label].item() for label in train_loader.dataset.labels]
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)
        train_loader = DataLoader(train_loader.dataset, batch_size=batch_size, sampler=sampler, num_workers=2)
        # Move class_weights to device for loss
        class_weights = class_weights.to(device)
        # Criterion: FocalLoss with class weighting
        criterion = FocalLoss(gamma=2.0, weight=class_weights)
        # Model selection
        if model_name == 'fusion':
            model = EdgeFusionCNN(num_classes=len(classes)).to(device)
        else:
            model = ImprovedBaselineCNN(num_classes=len(classes)).to(device)
        optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
        history = train_one_model(model, model_name, train_loader, val_loader, criterion, optimizer, scheduler, num_epochs, device)
        plot_history(history, model_name)
        # Save class names (once, after first model)
        if model_name == models_to_train[0]:
            os.makedirs('models', exist_ok=True)
            with open('models/class_names.json', 'w') as f:
                json.dump(classes, f)

if __name__ == '__main__':
    main()
