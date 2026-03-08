import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os

# Paths
base_dir = os.path.join(os.getcwd(), "model", "data")
train_dir = os.path.join(base_dir, "train")
test_dir = os.path.join(base_dir, "test")

# Image settings
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# Data generators
train_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)
train_data = train_datagen.flow_from_directory(
    train_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical", subset="training"
)
val_data = train_datagen.flow_from_directory(
    train_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical", subset="validation"
)
test_datagen = ImageDataGenerator(rescale=1./255)
test_data = test_datagen.flow_from_directory(
    test_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical"
)

# Model (EfficientNet transfer learning)
base_model = tf.keras.applications.EfficientNetB0(include_top=False, input_shape=(224,224,3), pooling="avg")
base_model.trainable = False

model = tf.keras.Sequential([
    base_model,
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(train_data.num_classes, activation="softmax")
])

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

# Train
history = model.fit(train_data, validation_data=val_data, epochs=5)

# Save model
save_path = os.path.join(os.getcwd(), "backend", "model_saved")
os.makedirs(save_path, exist_ok=True)
model.save(save_path)
print(f"✅ Model saved at {save_path}")
