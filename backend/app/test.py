#!/usr/bin/env python3
"""
test.py

Evaluate the trained model on the test dataset.
"""

import os
import torch
import torch.nn as nn
from torchvision import transforms

from app.dataset import (
    load_datasets,
    make_loaders,
    get_class_names,
    DEFAULT_TRANSFORM,
    TRAIN_DIR,
    TEST_DIR,
)
from app.model import build_model  # your model builder

# --------------------------
# ⚙️ Configuration
# --------------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 🧠 Automatically find model checkpoint
POSSIBLE_PATHS = [
    os.path.join(PROJECT_ROOT, "model.pth"),
    os.path.join(PROJECT_ROOT, "checkpoints", "best_model.pth"),
    os.path.join(PROJECT_ROOT, "model_saved", "model.pth"),
]

MODEL_PATH = next((p for p in POSSIBLE_PATHS if os.path.exists(p)), None)


def evaluate(batch_size: int = 32, num_workers: int = 0):
    """Evaluate the trained model on the test dataset."""

    # ✅ Load datasets using absolute paths
    _, _, test_dataset = load_datasets(
        train_dir=TRAIN_DIR,
        test_dir=TEST_DIR,
        transform=DEFAULT_TRANSFORM,
    )

    if test_dataset is None:
        print("❌ No test dataset found.")
        return

    # ✅ Create DataLoader
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    class_names = get_class_names(test_dataset)
    num_classes = len(class_names)

    # --------------------------
    # 🧩 Build model and load weights
    # --------------------------
    model = build_model(num_classes=num_classes)

    if MODEL_PATH:
        print(f"✅ Loading model weights from: {MODEL_PATH}")
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    else:
        print("⚠️ No model checkpoint found. Please train the model first.")
        return

    model.to(DEVICE)
    model.eval()

    # --------------------------
    # 📊 Evaluation loop
    # --------------------------
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    avg_loss = total_loss / len(test_loader)
    accuracy = correct / total

    print(f"\n📊 Test Loss: {avg_loss:.4f}")
    print(f"✅ Test Accuracy: {accuracy:.4f} ({correct}/{total})")


if __name__ == "__main__":
    print(f"🚀 Evaluating on {DEVICE} ...")
    evaluate()
