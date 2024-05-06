import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import io
import tempfile
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
import pathlib
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter
import io
import ffmpeg
import os 
import cProfile
import pstats
from memory_profiler import profile
import requests
import subprocess
from script_utils.util import is_video_valid, video_fetch_data, create_thumbnail


@profile
def create_thumbnail_from_url(video_url, output_file, time_offset):
    time_offset = min(float(time_offset), 60)
    ffmpeg_command = [
        'ffmpeg',
        '-ss', str(time_offset),
        '-i', video_url,
        '-vframes', '1',
        '-vf', 'scale=320:-1',
        '-y',  
        '-loglevel', 'error',  
        '-f', 'image2', 
        '-'
    ]
    try:
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        with open(output_file, 'wb') as f:
            f.write(result.stdout)  # Write the thumbnail image data to the output file
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode().strip()
        raise Exception(f"FFmpeg error: {error_message}") from e

# Add this to the bottom of your script
if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    indexdata = {'config': {'filename': '20184664-hd_1920_1080_30fps.mp4', 'indexfilename': '20184664hd_1920_1080_30fps_864c71b2-c543-4182-aace-aefb1b9deb14.mp4', 'id': 317}, 'processtype': 'video', 'md5': '6c2d4d673e232de1fee3c29328ebcf64', 'id_related': None}
    response = "https://aec18cb39d6670d41651478c21c17654.r2.cloudflarestorage.com/dev-content/2/20184664hd_1920_1080_30fps_6dd1475e-0e95-43e1-83e9-f32f217bfdc5.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=adeb2ecd1be24f028411893f758784c8%2F20240426%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240426T022330Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=ef52f42a450f96d68e9a05e2ecdb7ff75062e6d26bc113e24ca319495df63025"

    thumbnail_path = "./thumbnail/demo.jpg"
    video_data = is_video_valid(response)
    vidData = video_fetch_data(video_data)
    create_thumbnail_from_url(response, thumbnail_path, vidData["time_offset"])
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats()
