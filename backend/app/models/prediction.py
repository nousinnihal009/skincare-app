"""
prediction.py

ML Inference pipeline for skin condition classification.
Handles: model loading, image preprocessing, prediction, Grad-CAM heatmap generation.
"""

import os
import io
import base64
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import transforms
from PIL import Image

from app.model import build_model
from app.services.knowledge_base import get_condition_info, RISK_LEVELS

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Checkpoint paths to search (in priority order)
CHECKPOINT_PATHS = [
    os.path.join(BACKEND_DIR, "checkpoints", "best_model.pth"),
    os.path.join(BACKEND_DIR, "model_saved", "model.pth"),
    os.path.join(BACKEND_DIR, "model.pth"),
]

# Class names — must match the order used during training (sorted directory names)
CLASS_NAMES = [
    "Atopic Dermatitis",
    "Basal Cell Carcinoma (BCC)",
    "Benign Keratosis-like Lesions (BKL)",
    "Eczema",
    "Melanocytic Nevi (NV)",
    "Melanoma",
    "Psoriasis pictures Lichen Planus and related diseases",
    "Seborrheic Keratoses and other Benign Tumors",
    "Tinea Ringworm Candidiasis and other Fungal Infections",
    "Warts Molluscum and other Viral Infections",
    "acne-closed-comedo",
    "acne-cystic",
    "acne-excoriated",
    "acne-infantile",
    "acne-open-comedo",
    "acne-pustular",
    "acne-scar",
    "hidradenitis-suppurativa",
    "perioral-dermatitis",
    "pigmentation",
    "rosacea",
]

# Transform — MUST match training transforms exactly
INFERENCE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ─────────────────────────────────────────────────────────────
# Model Singleton
# ─────────────────────────────────────────────────────────────

_model = None
_model_loaded = False


def _find_checkpoint():
    """Find the first available model checkpoint."""
    for path in CHECKPOINT_PATHS:
        if os.path.exists(path):
            return path
    return None


def load_model():
    """Load model + weights. Called once at startup."""
    global _model, _model_loaded
    if _model_loaded:
        return _model

    num_classes = len(CLASS_NAMES)
    _model = build_model(num_classes=num_classes, pretrained=False)

    checkpoint_path = _find_checkpoint()
    if checkpoint_path is None:
        raise FileNotFoundError(
            f"No model checkpoint found. Searched: {CHECKPOINT_PATHS}"
        )

    print(f"Loading model from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE, weights_only=False)

    # Handle checkpoints saved with save_checkpoint() which wraps state_dict
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        state_dict = checkpoint["model_state"]
        print(f"  Checkpoint epoch: {checkpoint.get('epoch', '?')}, val_acc: {checkpoint.get('val_acc', '?')}")
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        # Direct state_dict save
        state_dict = checkpoint

    _model.load_state_dict(state_dict)
    _model.to(DEVICE)
    _model.eval()
    _model_loaded = True
    print(f"Model loaded successfully on {DEVICE}. Classes: {num_classes}")
    return _model


def get_model():
    """Get the loaded model (load if needed)."""
    if not _model_loaded:
        load_model()
    return _model


# ─────────────────────────────────────────────────────────────
# Grad-CAM
# ─────────────────────────────────────────────────────────────

class GradCAM:
    """Gradient-weighted Class Activation Mapping for ResNet50."""

    def __init__(self, model):
        self.model = model
        self.gradients = None
        self.activations = None
        self.hook_handles = []

    def _register_hooks(self):
        # ResNet50's last conv layer is layer4[-1].conv3
        target_layer = self.model.layer4[-1]

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        h1 = target_layer.register_forward_hook(forward_hook)
        h2 = target_layer.register_full_backward_hook(backward_hook)
        self.hook_handles = [h1, h2]

    def _remove_hooks(self):
        for h in self.hook_handles:
            h.remove()
        self.hook_handles = []

    def generate(self, input_tensor, class_idx=None):
        """Generate Grad-CAM heatmap."""
        self._register_hooks()

        self.model.eval()
        # Enable gradients for the input
        input_tensor.requires_grad_(True)

        output = self.model(input_tensor)

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        self.model.zero_grad()
        target = output[0, class_idx]
        target.backward()

        # Compute weights
        weights = self.gradients.mean(dim=[2, 3], keepdim=True)  # GAP
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)

        # Normalize
        cam = cam.squeeze().cpu().numpy()
        if cam.max() > 0:
            cam = cam / cam.max()

        self._remove_hooks()
        return cam


def generate_gradcam_overlay(image: Image.Image, cam: np.ndarray) -> str:
    """Generate a Grad-CAM heatmap overlay on the original image.
    Returns base64 encoded PNG."""
    import colorsys

    img = image.resize((224, 224))
    img_array = np.array(img, dtype=np.float32) / 255.0

    # Resize CAM to image size
    from PIL import Image as PILImage
    cam_resized = np.array(
        PILImage.fromarray((cam * 255).astype(np.uint8)).resize((224, 224), PILImage.BILINEAR)
    ).astype(np.float32) / 255.0

    # Create heatmap using jet-like colormap
    heatmap = np.zeros((*cam_resized.shape, 3), dtype=np.float32)
    for i in range(cam_resized.shape[0]):
        for j in range(cam_resized.shape[1]):
            val = cam_resized[i, j]
            # Blue → Cyan → Green → Yellow → Red
            if val < 0.25:
                r, g, b = 0, val * 4, 1.0
            elif val < 0.5:
                r, g, b = 0, 1.0, 1.0 - (val - 0.25) * 4
            elif val < 0.75:
                r, g, b = (val - 0.5) * 4, 1.0, 0
            else:
                r, g, b = 1.0, 1.0 - (val - 0.75) * 4, 0
            heatmap[i, j] = [r, g, b]

    # Overlay
    alpha = 0.4
    overlay = img_array * (1 - alpha) + heatmap * alpha
    overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)

    # Encode as base64
    overlay_img = Image.fromarray(overlay)
    buffer = io.BytesIO()
    overlay_img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ─────────────────────────────────────────────────────────────
# Main Prediction Function
# ─────────────────────────────────────────────────────────────

def predict_condition(image_bytes) -> dict:
    """
    Full inference pipeline:
    Image → Validation → Preprocessing → Model → Confidence → Top-3 → Risk → Grad-CAM → Results
    """
    model = get_model()

    # 1. Open and validate the image
    image = Image.open(image_bytes).convert("RGB")

    # 2. Preprocess
    input_tensor = INFERENCE_TRANSFORM(image).unsqueeze(0).to(DEVICE)

    # 3. Model inference
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = F.softmax(outputs, dim=1)

    probs = probabilities.squeeze().cpu().numpy()

    # 4. Top-3 predictions
    top3_indices = probs.argsort()[::-1][:3]
    top3_predictions = []
    for idx in top3_indices:
        class_name = CLASS_NAMES[idx]
        info = get_condition_info(class_name)
        top3_predictions.append({
            "class_name": class_name,
            "display_name": info["display_name"],
            "confidence": float(probs[idx]),
            "category": info["category"],
        })

    # 5. Primary prediction details
    primary_idx = top3_indices[0]
    primary_class = CLASS_NAMES[primary_idx]
    primary_confidence = float(probs[primary_idx])
    primary_info = get_condition_info(primary_class)

    # 6. Risk assessment
    risk_level = primary_info.get("risk_level", "moderate")
    risk_info = RISK_LEVELS.get(risk_level, RISK_LEVELS["moderate"])

    # Adjust risk based on confidence
    is_high_risk_condition = primary_info.get("is_cancerous", False)
    urgency = primary_info.get("urgency", "routine")

    # 7. Generate Grad-CAM heatmap
    gradcam_base64 = None
    try:
        gradcam = GradCAM(model)
        input_for_cam = INFERENCE_TRANSFORM(image).unsqueeze(0).to(DEVICE)
        cam = gradcam.generate(input_for_cam, class_idx=primary_idx)
        gradcam_base64 = generate_gradcam_overlay(image, cam)
    except Exception as e:
        print(f"Grad-CAM generation failed: {e}")

    # 8. Build response
    result = {
        "prediction": {
            "class_name": primary_class,
            "display_name": primary_info["display_name"],
            "confidence": primary_confidence,
            "category": primary_info["category"],
        },
        "top3": top3_predictions,
        "risk_assessment": {
            "level": risk_level,
            "label": risk_info["label"],
            "color": risk_info["color"],
            "action": risk_info["action"],
            "is_cancerous": is_high_risk_condition,
            "urgency": urgency,
        },
        "condition_info": {
            "description": primary_info["description"],
            "severity": primary_info.get("severity", "unknown"),
            "causes": primary_info.get("causes", []),
            "symptoms": primary_info.get("symptoms", []),
            "medical_explanation": primary_info.get("medical_explanation", ""),
            "when_to_see_doctor": primary_info.get("when_to_see_doctor", ""),
        },
        "treatments": primary_info.get("treatments", {}),
        "skincare_routine": primary_info.get("skincare_routine", {}),
        "gradcam_heatmap": gradcam_base64,
        "confidence_distribution": {
            CLASS_NAMES[i]: float(probs[i]) for i in probs.argsort()[::-1][:5]
        },
        "disclaimer": (
            "⚠️ This analysis is generated by an AI system and is NOT a medical diagnosis. "
            "It is intended for educational and informational purposes only. "
            "Please consult a qualified dermatologist for professional medical advice, "
            "diagnosis, and treatment."
        ),
    }

    # Add urgent warning for high-risk conditions
    if is_high_risk_condition and primary_confidence > 0.3:
        result["urgent_warning"] = (
            f"⚠️ HIGH RISK DETECTED — The AI has detected signs consistent with "
            f"{primary_info['display_name']}, which may be a serious condition. "
            f"Please consult a dermatologist IMMEDIATELY for professional evaluation."
        )

    return result
