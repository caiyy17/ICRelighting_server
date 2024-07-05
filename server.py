from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
import base64
import io
from PIL import Image
from flask import jsonify
import time

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
    start = time.time()
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(filepath)

    print('Image successfully uploaded')

    results = comfy_api.comfy_generate(filepath)

    # 在这里处理图像并生成四张Base64图片（此处为示例，实际处理可能不同）
    base64_images = []
    image_node = ["152", "152", "152", "152", "153"]
    image_index = [0, 1, 3, 2, 0]
    for i in range(5):
        buffer = io.BytesIO()
        Image.open(io.BytesIO(results[image_node[i]][image_index[i]])).save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        base64_images.append(base64_image)
    
    response_data = {
        "message": "Image received successfully",
        "status": "success",
        "images": base64_images
    }
    print('time taken to process image:', time.time() - start)
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

##################################################
# Video
##################################################

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS_V = {'mp4', 'mov', 'avi', 'mkv'}

def allowed_file_v(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_V

@app.route('/uploadv', methods=['POST'])
def upload_file_v():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file_v(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print('File successfully uploaded')

        frame_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'frames')
        # 删除现有的帧文件夹
        if os.path.exists(frame_folder):
            os.system(f"rm -r {frame_folder}")
        os.makedirs(frame_folder)

        # 将视频文件转换为PNG图片
        output_frame_pattern = os.path.join(frame_folder, 'frame_%04d.png')
        ffmpeg_command = f"ffmpeg -i {filepath} -vf fps=8 {output_frame_pattern} -y"
        # ffmpeg_command = f"ffmpeg -i {filepath} {output_frame_pattern} -y"
        os.system(ffmpeg_command)
        print('All frames successfully extracted at 30fps')

        return 'File successfully uploaded and converted'
    else:
        return 'Allowed file types are mp4, mov, avi, mkv'

@app.route('/processv', methods=['POST'])
def process_video():
    start = time.time()
    out_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'out_frames')
        # 删除现有的帧文件夹
    if os.path.exists(out_folder):
        os.system(f"rm -r {out_folder}")
    os.makedirs(out_folder)
    os.makedirs(os.path.join(out_folder, 'out1'))
    os.makedirs(os.path.join(out_folder, 'out2'))
    os.makedirs(os.path.join(out_folder, 'out3'))
    os.makedirs(os.path.join(out_folder, 'out4'))
    os.makedirs(os.path.join(out_folder, 'out5'))

    # all image in os.path.join(frame_folder, 'frame_%04d.png')
    for filename in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'frames')):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'frames', filename)
        if filename.endswith('.png'):
            results = comfy_api.comfy_generate(filepath)
            image_node = ["152", "152", "152", "152", "153"]
            image_index = [0, 1, 3, 2, 0]
            for i in range(5):
                image= Image.open(io.BytesIO(results[image_node[i]][image_index[i]]))
                image.save(os.path.join(out_folder, f'out{i+1}', filename))
            print(f'Frame {filename} successfully processed')
            # wait for 1 second
            time.sleep(1)
    sync_image_v()
    print('time taken to process video:', time.time() - start)
    return 'Video successfully processed'

@app.route('/sync_v', methods=['POST'])
def sync_image_v():
    out_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'out_frames')
    if not os.path.exists(out_folder):
        return jsonify({"error": "No video data"})
    # 将处理后的图片转换为视频
    base64_videos = []
    output_video_pattern = os.path.join(app.config['UPLOAD_FOLDER'], 'out_%d.mp4')
    for i in range(5):
        ffmpeg_command = f"ffmpeg -framerate 8 -i {os.path.join(out_folder, f'out{i+1}', 'frame_%04d.png')} -vcodec libx264 -profile:v high -preset slow -crf 22 -pix_fmt yuv420p -acodec aac -b:a 192k {output_video_pattern % (i+1)} -y"
        os.system(ffmpeg_command)
        print(f'Video {i+1} successfully generated')

        # 用os将mp4视频转换为Base64
        buffer = io.BytesIO()
        with open(output_video_pattern % (i+1), 'rb') as f:
            buffer.write(f.read())
        base64_video = base64.b64encode(buffer.getvalue()).decode('utf-8')
        base64_videos.append(base64_video)

    response_data = {
        "message": "Video successfully processed",
        "status": "success",
        "images": base64_videos
    }
    print("Video send successfully")
    return jsonify(response_data)

if __name__ == '__main__':
    # make sure the folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5002, host='0.0.0.0')