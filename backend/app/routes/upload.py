from fastapi import APIRouter, File, UploadFile

router = APIRouter()

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    filename = file.filename
    return {"status": "success", "received_file": filename}
