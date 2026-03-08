#!/usr/bin/env python3
"""
train.py

Advanced training pipeline for the Skin Lesion Classification project.
- Loads data dynamically from dataset.py
- Loads hyperparameters from config.yaml
- Trains and validates using progress bars, checkpointing, and logging
"""

import os
import sys
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

# Allow importing from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dataset import load_datasets, make_loaders, get_class_names, DEFAULT_TRANSFORM, TRAIN_DIR, TEST_DIR
from app.model import build_model


# ---------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------
def load_config(config_path="config.yaml"):
    """Load training configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"❌ Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_checkpoint(model, optimizer, epoch, val_acc, path):
    """Save model checkpoint."""
    state = {
        "epoch": epoch,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "val_acc": val_acc,
    }
    torch.save(state, path)
    print(f"💾 Saved checkpoint: {path}")


# ---------------------------------------------------------------
# Main Training Function
# ---------------------------------------------------------------
def train_model(config_path="config.yaml"):
    """Train model using configuration from YAML."""
    # Load config
    cfg = load_config(config_path)

    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔥 Using device: {device}")

    # Parameters
    epochs = cfg["training"]["epochs"]
    batch_size = cfg["training"]["batch_size"]
    lr = cfg["training"]["learning_rate"]
    val_split = cfg["training"]["val_split"]
    save_dir = cfg["training"]["save_dir"]
    log_dir = cfg["training"]["log_dir"]

    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # Load datasets & dataloaders
    print("📦 Loading datasets...")
    train_ds, val_ds, test_ds = load_datasets(TRAIN_DIR, TEST_DIR, DEFAULT_TRANSFORM, val_split=val_split)
    train_loader, val_loader, _ = make_loaders(train_ds, val_ds, test_ds, batch_size=batch_size, num_workers=0)

    class_names = get_class_names(train_ds)
    num_classes = len(class_names)
    print(f"🧩 Classes: {num_classes} | {class_names}")

    # Build model
    model = build_model(num_classes=num_classes, pretrained=True).to(device)

    # Loss, optimizer, and logging
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    writer = SummaryWriter(log_dir=log_dir)

    best_val_acc = 0.0

    # ---------------------------------------------------------------
    # Training Loop
    # ---------------------------------------------------------------
    print("\n🚀 Starting training...\n")
    for epoch in range(epochs):
        model.train()
        running_loss, correct, total = 0.0, 0, 0

        loop = tqdm(train_loader, desc=f"Epoch [{epoch+1}/{epochs}]", leave=False)
        for images, labels in loop:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            loop.set_postfix(loss=loss.item())

        train_loss = running_loss / total
        train_acc = correct / total

        # ---------------------------------------------------------------
        # Validation
        # ---------------------------------------------------------------
        val_loss, val_correct, val_total = 0.0, 0, 0
        model.eval()
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_loss /= val_total
        val_acc = val_correct / val_total

        # Logging
        writer.add_scalar("Loss/train", train_loss, epoch)
        writer.add_scalar("Loss/val", val_loss, epoch)
        writer.add_scalar("Acc/train", train_acc, epoch)
        writer.add_scalar("Acc/val", val_acc, epoch)

        print(f"📊 Epoch [{epoch+1}/{epochs}] | "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

        # ---------------------------------------------------------------
        # Save best model
        # ---------------------------------------------------------------
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint_path = os.path.join(save_dir, "best_model.pth")
            save_checkpoint(model, optimizer, epoch, val_acc, checkpoint_path)
            print("✅ New best model saved!")

    writer.close()
    print("\n🎉 Training completed successfully!")


# ---------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------
if __name__ == "__main__":
    train_model("config.yaml")
