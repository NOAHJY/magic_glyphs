from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import base64
import io
import os
import torch
import torchvision.transforms as T
import torchvision.models as models
import time

app = Flask(__name__)
CORS(app)

# Load pretrained ResNet18 model
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.eval()

# Remove final classification layer to get feature vectors
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

# Image transformation
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
])


def preprocess(img: Image.Image):
    """Remove transparency and convert to grayscale."""
    # Convert to RGBA to handle transparent backgrounds
    img = img.convert("RGBA")

    # Create a white background
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))

    # Paste original image onto white background using alpha channel
    background.paste(img, mask=img.split()[3])

    # Convert to grayscale
    img = background.convert("L")

    return img


def get_features(img: Image.Image):
    """Convert a PIL image to a 512-dimensional feature vector."""
    # Preprocess image
    img = preprocess(img)

    # ResNet expects RGB input
    img = img.convert("RGB")

    # Convert image to tensor
    tensor = transform(img).unsqueeze(0)

    # Extract features
    with torch.no_grad():
        features = feature_extractor(tensor)

    # Flatten to shape [512]
    return features.squeeze()


def load_glyphs():
    """Load all glyph images from the glyphs folder."""
    glyphs = {}
    glyphs_dir = os.path.join(os.path.dirname(__file__), "glyphs")

    for filename in os.listdir(glyphs_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(glyphs_dir, filename)
            img = Image.open(path)

            # Filename without extension becomes glyph name
            name = os.path.splitext(filename)[0]

            # Extract and store features
            glyphs[name] = get_features(img)

    return glyphs


# Preload glyphs at startup
GLYPHS = load_glyphs()

current_command = None

MESSAGES = {
    'light': 'Light',
    'star': "Star",
    'love': "Love",
    # add more here, name must match your image filename
}


ESP32_IP = "http://192.168.1.100"  # change later

ESP32_ACTIONS = {
    'light': '/light',
    'star': '/star',
    'love': '/love',
}


@app.route("/detect", methods=["POST"])
def detect():
    # Get JSON data from browser
    data = request.json
    image_base64 = data["image"]

    # Remove data URL prefix if present
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    # Decode base64 image
    image_bytes = base64.b64decode(image_base64)
    drawn_img = Image.open(io.BytesIO(image_bytes))

    # Extract features from drawn image
    drawn_features = get_features(drawn_img)

    # Find best matching glyph
    best_match = None
    best_score = -1.0

    for name, glyph_features in GLYPHS.items():
        score = torch.nn.functional.cosine_similarity(
            drawn_features.unsqueeze(0),
            glyph_features.unsqueeze(0)
        ).item()

        if score > best_score:
            best_score = score
            best_match = name

    # Return result
    # message = MESSAGES.get(best_match, 'An unknown sigil stirs...')
    
    action = ESP32_ACTIONS.get(best_match)
    if action and best_score >= 0.75:
        global current_command
        current_command = action

    return jsonify({
        'match': best_match,
        'similarity': round(best_score, 4),
        'message': message
    })

@app.route('/get-command', methods=['GET'])
def get_command():
    global current_command
    timeout = 25  # seconds
    elapsed = 0
    
    while current_command is None and elapsed < timeout:
        time.sleep(0.5)
        elapsed += 0.5
    
    cmd = current_command
    current_command = None
    return jsonify({ 'command': cmd })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
