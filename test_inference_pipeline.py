import sys
import os
import base64
from PIL import Image
import io

# Add backend to path so we can import app modules
original_dir = os.getcwd()
backend_dir = os.path.join(original_dir, "backend")
sys.path.append(backend_dir)

from app.models.prediction import predict_condition

def test_inference():
    print("Testing ML inference pipeline...")
    
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color = (73, 109, 137))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    try:
        result = predict_condition(img_bytes)
        print("✅ Inference pipeline ran successfully")
        print(f"Top prediction: {result['prediction']['class_name']} ({result['prediction']['confidence']:.2%})")
        print(f"Risk level: {result['risk_assessment']['level']}")
        
        # Check Grad-CAM
        heatmap_base64 = result.get("gradcam_heatmap")
        if heatmap_base64:
            print("✅ Grad-CAM heatmap generated successfully")
            
            # Save it to check visually
            heatmap_data = base64.b64decode(heatmap_base64)
            with open("test_gradcam.png", "wb") as f:
                f.write(heatmap_data)
            print("Saved to test_gradcam.png")
        else:
            print("❌ Grad-CAM heatmap missing")
            
    except Exception as e:
        import traceback
        print("❌ Inference pipeline failed:")
        traceback.print_exc()

if __name__ == "__main__":
    test_inference()
