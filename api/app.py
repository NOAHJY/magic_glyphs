from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import base64
import io
import os
import torch
import torchvision.transforms as T
import torchvision.models as models

app = Flask(__name__)
CORS(app)

# Load a pretrained model to extract image features
model = models.resnet18(pretrained=True)
model.eval()
# Remove the final classification layer — we just want features
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
])

def get_features(img: Image.Image):
    """Convert a PIL image to a feature vector."""
    img = img.convert("RGB")
    tensor = transform(img).unsqueeze(0)  # shape: [1, 3, 224, 224]
    with torch.no_grad():
        features = feature_extractor(tensor)
    return features.squeeze()  # shape: [512]

def load_glyphs():
    """Load all glyph images from the glyphs/ folder."""
    glyphs = {}
    glyphs_dir = os.path.join(os.path.dirname(__file__), 'glyphs')
    for filename in os.listdir(glyphs_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(glyphs_dir, filename)
            img = Image.open(path)
            name = os.path.splitext(filename)[0]  # e.g. "fire", "water"
            glyphs[name] = get_features(img)
    return glyphs

# Pre-load glyphs at startup
GLYPHS = load_glyphs()

@app.route('/detect', methods=['POST'])
def detect():
    # 1. Get the image from the browser
    data = request.json
    image_base64 = data['image']  # ✅ fixed key!

    # 2. Strip the data URL header (e.g. "data:image/png;base64,...")
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]

    # 3. Decode base64 → PIL Image
    image_bytes = base64.b64decode(image_base64)
    drawn_img = Image.open(io.BytesIO(image_bytes))

    # 4. Get features of the drawn image
    drawn_features = get_features(drawn_img)

    # 5. Compare against every glyph using cosine similarity
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

    return jsonify({
        'match': best_match,
        'similarity': round(best_score, 4)
    })

if __name__ == '__main__':
    app.run(debug=True)
