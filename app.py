from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import base64
import torch

app = Flask(__name__)
CORS(app)  # allows browser to talk to Python

@app.route('/detect', methods=['POST'])
def detect():
    # 1. Get the image data from the browser
    data = request.json
    image_base64 = data['???']  # what key did we send from JavaScript?
    
    return jsonify({ 'similarity': 0.0 })

if __name__ == '__main__':
    app.run(debug=True)