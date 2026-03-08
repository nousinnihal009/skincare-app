"""
analysis.py — Skin Analysis API routes
"""

import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.prediction import predict_condition

router = APIRouter(prefix="/api", tags=["analysis"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/analyze")
async def analyze_skin(file: UploadFile = File(...)):
    """Full skin analysis: image → model inference → Grad-CAM → risk assessment → results."""

    # Validate file type
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Run prediction
    try:
        image_bytes = io.BytesIO(contents)
        result = predict_condition(image_bytes)
        result["received_file"] = filename
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
