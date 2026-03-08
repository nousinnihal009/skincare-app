#!/usr/bin/env python3
"""
dataset.py

Resolves the project-root `data/` path, loads torchvision.datasets.ImageFolder
for train/test, optionally splits train -> train/val, and provides DataLoader
objects. Safe defaults for Windows (num_workers=0).

Usage (examples):
  python app/dataset.py                    # prints dataset info
  python app/dataset.py --val-split 0.2    # create a 20% validation split
  python app/dataset.py --batch-size 16 --num-workers 0

When imported this module exposes (with default args):
  train_dataset, val_dataset (or None), test_dataset (or None)
  train_loader, val_loader (or None), test_loader (or None)
  class_names

Keep in mind: torchvision.datasets.ImageFolder expects the directory layout:
  data/
    train/
      class_a/
      class_b/
    test/
      class_a/
      class_b/

"""

import os
import argparse
from typing import Optional, Tuple

import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split


def _resolve_paths() -> Tuple[str, str, str, str]:
    """Return (project_root, data_dir, train_dir, test_dir).

    This file lives at: <project>/backend/app/dataset.py
    so project root is two levels up from __file__.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(project_root, "data")
    train_dir = os.path.join(data_dir, "train")
    test_dir = os.path.join(data_dir, "test")
    return project_root, data_dir, train_dir, test_dir


# Default image transforms (ImageNet-style normalization)
DEFAULT_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),  # standard for many CNNs
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


def load_datasets(
    train_dir: str,
    test_dir: str,
    transform: transforms.Compose = DEFAULT_TRANSFORM,
    val_split: float = 0.0,
    seed: int = 42,
):
    """Load ImageFolder datasets and optionally split a validation set.

    Returns: (train_dataset, val_dataset_or_None, test_dataset_or_None)
    """
    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"Training directory not found: {train_dir}")

    # load full training dataset (ImageFolder requires class subfolders)
    full_train = datasets.ImageFolder(train_dir, transform=transform)

    val_dataset = None
    train_dataset = full_train

    if val_split and 0.0 < val_split < 1.0:
        total = len(full_train)
        n_val = int(total * val_split)
        n_train = total - n_val
        if n_val == 0 or n_train == 0:
            raise ValueError("val_split too small or too large for the number of samples")
        generator = torch.Generator().manual_seed(seed)
        train_dataset, val_dataset = random_split(full_train, [n_train, n_val], generator=generator)

    test_dataset = None
    if os.path.exists(test_dir):
        test_dataset = datasets.ImageFolder(test_dir, transform=transform)

    return train_dataset, val_dataset, test_dataset


def make_loaders(
    train_dataset,
    val_dataset,
    test_dataset,
    batch_size: int = 32,
    num_workers: int = 0,
    pin_memory: Optional[bool] = None,
):
    """Create DataLoader objects. Use num_workers=0 by default on Windows.

    Returns: (train_loader, val_loader_or_None, test_loader_or_None)
    """
    if pin_memory is None:
        pin_memory = torch.cuda.is_available()

    # Determine whether each dataset is a Subset (random_split) or an ImageFolder
    def _is_subset(ds):
        return hasattr(ds, "indices") or type(ds).__name__ == "Subset"

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    val_loader = None
    if val_dataset is not None:
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        )

    test_loader = None
    if test_dataset is not None:
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        )

    return train_loader, val_loader, test_loader


def get_class_names(dataset) -> Optional[list]:
    """Return class names even if dataset is a Subset from random_split."""
    if dataset is None:
        return None
    if hasattr(dataset, "classes"):
        return dataset.classes
    # Subset created by random_split has .dataset pointing to the underlying ImageFolder
    if hasattr(dataset, "dataset") and hasattr(dataset.dataset, "classes"):
        return dataset.dataset.classes
    return None


# When module is imported, provide a sane default so other modules can import loaders:
PROJECT_ROOT, DATA_DIR, TRAIN_DIR, TEST_DIR = _resolve_paths()

# sensible defaults
try:
    _train_dataset, _val_dataset, _test_dataset = load_datasets(TRAIN_DIR, TEST_DIR, DEFAULT_TRANSFORM, val_split=0.0)
except FileNotFoundError:
    # keep variables defined but empty so imports won't crash; user can call load_datasets manually
    _train_dataset, _val_dataset, _test_dataset = None, None, None

_train_loader, _val_loader, _test_loader = (None, None, None)
if _train_dataset is not None:
    _train_loader, _val_loader, _test_loader = make_loaders(_train_dataset, _val_dataset, _test_dataset, batch_size=32, num_workers=0)

class_names = get_class_names(_train_dataset) or []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect and optionally create dataloaders for the project dataset")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=0, help="Use 0 on Windows to avoid multiprocessing issues")
    parser.add_argument("--val-split", type=float, default=0.0, help="Fraction of training set to reserve for validation (0-1)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("🔎 Project root:", PROJECT_ROOT)
    print("🔎 Looking for data in:", DATA_DIR)
    print("🔎 Train dir:", TRAIN_DIR)
    print("🔎 Test dir:", TEST_DIR)

    try:
        train_ds, val_ds, test_ds = load_datasets(TRAIN_DIR, TEST_DIR, DEFAULT_TRANSFORM, val_split=args.val_split, seed=args.seed)
    except Exception as e:
        print("❌ Error while loading datasets:", e)
        raise

    train_loader, val_loader, test_loader = make_loaders(train_ds, val_ds, test_ds, batch_size=args.batch_size, num_workers=args.num_workers)

    names = get_class_names(train_ds) or []
    n_train = len(train_ds) if train_ds is not None else 0
    n_val = len(val_ds) if val_ds is not None else 0
    n_test = len(test_ds) if test_ds is not None else 0

    print(f"✅ Found {n_train} training samples across {len(names)} classes.")
    if args.val_split and val_ds is not None:
        print(f"✅ Validation samples: {n_val} ({args.val_split*100:.1f}% split)")
    print(f"✅ Found {n_test} testing samples.")
    print("📂 Classes:", names)

    print("\nLoaders summary:")
    print(" - train_loader:", train_loader)
    print(" - val_loader:", val_loader)
    print(" - test_loader:", test_loader)

    print("\nDone.")
