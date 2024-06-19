from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
import base64
import io
from PIL import Image
from flask import jsonify

import comfy_api as comfy_api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print('File successfully uploaded')
        # change it into png, -y is to overwrite the existing file
        os.system(f"ffmpeg -i {UPLOAD_FOLDER + filename} {UPLOAD_FOLDER}image.png -y")
        print('File successfully converted')
        return 'File successfully uploaded'
    else:
        return 'Allowed file types are png, jpg, jpeg, gif'

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(filepath)

    comfy_api.comfy_generate(filepath)

    # 在这里处理图像并生成四张Base64图片（此处为示例，实际处理可能不同）
    base64_images = []
    image_names = ["152_0.png", "152_1.png", "152_3.png", "152_2.png", "153_0.png"]
    for i in range(5):
        buffer = io.BytesIO()
        Image.open(UPLOAD_FOLDER + f"output_{image_names[i]}").save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        base64_images.append(base64_image)
    
    response_data = {
        "message": "Image received successfully",
        "status": "success",
        "images": base64_images
    }
    
    return jsonify(response_data)

@app.route('/sync', methods=['POST'])
def sync_image():
    image_name = UPLOAD_FOLDER + "image.png"
    buffer = io.BytesIO()
    Image.open(image_name).save(buffer, format="PNG")
    base64_images = []
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    base64_images.append(base64_image)

    response_data = {
        "message": "Image send successfully",
        "status": "success",
        "images": base64_images
    }
    print("Image send successfully")
    return jsonify(response_data)

if __name__ == '__main__':
    # make sure the folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5002, host='0.0.0.0')