#!/usr/bin/env python3
"""
model.py

Defines the CNN model for skin condition classification.
We use transfer learning with torchvision's ResNet50 backbone.
"""

import torch
import torch.nn as nn
import torchvision.models as models


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    """
    Build a ResNet50 model for classification.

    Args:
        num_classes (int): Number of output classes.
        pretrained (bool): Whether to use ImageNet pretrained weights.

    Returns:
        nn.Module: The classification model.
    """
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None)

    # Replace the final classification layer
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes)
    )
    return model


if __name__ == "__main__":
    # Quick test
    num_classes = 21  # adjust later if needed
    model = build_model(num_classes)
    x = torch.randn(2, 3, 224, 224)
    y = model(x)
    print("✅ Model built. Output shape:", y.shape)  # should be [2, 21]
