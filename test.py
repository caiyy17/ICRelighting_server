from werkzeug.utils import secure_filename
import os
import base64
import io
from PIL import Image
from flask import jsonify
import time

import comfy_api as comfy_api

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def process_video():
    start = time.time()
    out_folder = os.path.join(UPLOAD_FOLDER, 'out_frames')
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
    list = os.listdir(os.path.join(UPLOAD_FOLDER, 'frames'))
    list.sort()
    print(list)
    for filename in list:
        filepath = os.path.join(UPLOAD_FOLDER, 'frames', filename)
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

def sync_image_v():
    out_folder = os.path.join(UPLOAD_FOLDER, 'out_frames')
    if not os.path.exists(out_folder):
        return jsonify({"error": "No video data"})
    # 将处理后的图片转换为视频
    base64_videos = []
    output_video_pattern = os.path.join(UPLOAD_FOLDER, 'out_%d.mp4')
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

process_video()