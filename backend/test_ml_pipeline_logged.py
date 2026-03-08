import os
import sys
import traceback
import json
import logging
import io

# Configure logger to write directly to file from within Python
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python_execution.log')
logging.basicConfig(filename=log_file, level=logging.INFO, filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Script started")

try:
    # Add backend to path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    logger.info("Loading model...")
    from app.models.prediction import load_model, predict_condition
    
    # Force load
    load_model()
    logger.info("Model loaded successfully!")
    
    # Find a test image - use the correct path
    project_root = os.path.dirname(backend_dir)  # skincare-app root
    test_image_dir = os.path.join(project_root, "data", "test", "Melanoma")
    logger.info(f"Looking for test images in: {test_image_dir}")
    
    test_images = [f for f in os.listdir(test_image_dir) if f.endswith('.jpg')]
    
    if not test_images:
        logger.error(f"No test images found in {test_image_dir}")
        sys.exit(1)
        
    test_image_path = os.path.join(test_image_dir, test_images[0])
    logger.info(f"Running prediction on {test_image_path}...")
    
    # Read image bytes
    with open(test_image_path, "rb") as f:
        image_bytes = io.BytesIO(f.read())
        
    # Predict
    result = predict_condition(image_bytes)
    
    # Save output
    output_path = os.path.join(backend_dir, "prediction_test_result.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)
        
    logger.info(f"SUCCESS! Prediction: {result['prediction']['display_name']} ({result['prediction']['confidence']:.2%})")
    logger.info(f"Risk: {result['risk_assessment']['level']}")
    top3_str = ", ".join([f"{p['display_name']} ({p['confidence']:.2%})" for p in result['top3']])
    logger.info(f"Top-3: {top3_str}")
    logger.info(f"Grad-CAM generated: {'Yes' if result.get('gradcam_heatmap') else 'No'}")
    logger.info(f"Results saved to {output_path}")
    print(f"SUCCESS: {result['prediction']['display_name']} ({result['prediction']['confidence']:.2%})")

except Exception as e:
    logger.error(f"FAILED: {e}")
    logger.error(traceback.format_exc())
    print(f"FAILED: {e}")
