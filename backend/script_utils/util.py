import sys

sys.path.append("..")

import boto3
import os
import requests
import ffmpeg
import subprocess
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import pathlib
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter
import io
import tempfile
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from utils import *
import decimal
from boto3.s3.transfer import TransferConfig
import warnings

warnings.filterwarnings('ignore')


def is_video_valid(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        if "streams" in probe.keys() and len(probe["streams"]) > 0:
            return probe
    except ffmpeg.Error:
        pass
    return False
    
def create_thumbnail(video_url, output_file, time_offset):
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
            f.write(result.stdout) 
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode().strip()
        raise Exception(f"FFmpeg error: {error_message}") from e


def create_thumbnail_image(output_file):
    img = Image.open(output_file)
    img = img.convert("RGB")
    width, height = img.size
    aspect_ratio = width / height
    if abs(aspect_ratio - 1.7777) > 0.5:
        bg_blur = img.resize((960, 540))
        blurred = bg_blur.filter(ImageFilter.GaussianBlur(52))
        bg_blur.paste(blurred, (0, 0))
        main_img = img.resize((int(540 * aspect_ratio), 540))
        bg_blur.paste(main_img, (int((960 - (540 * aspect_ratio)) / 2), 0))
        bg_blur.save(output_file, quality=50)


def lower_resolution(image_file):
    try:
        image = cv2.imread(image_file)
        height, width, _ = image.shape
        if width > 960 or height > 540:
            aspect_ratio = width / height
            if aspect_ratio > 16 / 9:
                new_width = 960
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = 540
                new_width = int(new_height * aspect_ratio)
            resized_image = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_AREA
            )
            cv2.imwrite(image_file, resized_image)
    except FileNotFoundError:
        raise FileNotFoundError("Image file not found.")

metadata_s3 = boto3.client(
    "s3",
    aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
    aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
    endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
    config=boto3.session.Config(signature_version="s3v4"),
)

def thumbnail_upload(filepath, s3 = metadata_s3):
    try:
        GB = 1024 ** 3
        config = TransferConfig(multipart_threshold=5 * GB, max_concurrency=5)
        s3.upload_file(filepath, CLOUDFLARE_METADATA, filepath, Config=config)
    except FileNotFoundError:
        raise FileNotFoundError("Image file not found.")
    except Exception as e:
        raise e


def convert_seconds(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    time_format = "{:02d}:{:02d}:{:02d}".format(hours, minutes, remaining_seconds)
    return time_format


def niceBytes(x: str) -> str:
    units = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    l = 0
    n = int(x)
    while n >= 1024 and l < len(units) - 1:
        n = n / 1024
        l += 1
    rounded_n = decimal.Decimal(n).quantize(decimal.Decimal("0.00"))
    return f"{rounded_n} {units[l]}"


def niceMB(x: str) -> str:
    x = str(x)
    units = ["MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    l = 0
    n = float(x) if x.replace(".", "", 1).isdigit() else 0
    while n >= 1000 and l < len(units) - 1:
        n = n / 1000
        l += 1
    rounded_n = decimal.Decimal(n)
    rounded_n = round(rounded_n, 2)
    return f"{rounded_n} {units[l]}"


def nice_unit(x: str) -> str:
    unit = str(x).split(" ")[-1]
    if str(x).split(" ")[0].split(".")[-1] == "00":
        x = str(x).split(".")[0] + " " + unit
    return x


def video_fetch_data(data):
    filename = urljoin(
        data["format"]["filename"], urlparse(data["format"]["filename"]).path
    )
    file_ext = filename.split(".")[-1]
    if file_ext == "mov":
        return {
            "width": data["streams"][1]["width"],
            "height": data["streams"][1]["height"],
            "frame_rate": eval(data["streams"][1]["r_frame_rate"]),
            "duration": data["format"]["duration"],
            "filesize": data["format"]["size"],
            "middle_time": float(data["format"]["duration"]) / 4,
            "time_offset": f"{float(data['format']['duration'])/4:.2f}",
        }
    elif file_ext == "mp4":
        return {
            "width": data["streams"][0]["width"],
            "height": data["streams"][0]["height"],
            "frame_rate": eval(data["streams"][0]["r_frame_rate"]),
            "duration": data["format"]["duration"],
            "filesize": data["format"]["size"],
            "middle_time": float(data["format"]["duration"]) / 4,
            "time_offset": f"{float(data['format']['duration'])/4:.2f}",
        }
    elif file_ext == "webm":
        return {
            "width": data["streams"][0]["width"],
            "height": data["streams"][0]["height"],
            "frame_rate": eval(data["streams"][0]["r_frame_rate"]),
            "duration": data["format"]["duration"],
            "filesize": data["format"]["size"],
            "middle_time": float(data["format"]["duration"]) / 4,
            "time_offset": f"{float(data['format']['duration'])/4:.2f}",
        }
    elif file_ext == "mkv":
        return {
            "width": data["streams"][0]["width"],
            "height": data["streams"][0]["height"],
            "frame_rate": eval(data["streams"][0]["r_frame_rate"]),
            "duration": data["format"]["duration"],
            "filesize": data["format"]["size"],
            "middle_time": float(data["format"]["duration"]) / 4,
            "time_offset": f"{float(data['format']['duration'])/4:.2f}",
        }


def lower_resolution_image(img_link, image_thumbnail_path):
    try:
        r = requests.get(img_link, allow_redirects=True)
        open(image_thumbnail_path, "wb").write(r.content)
        img_size = os.path.getsize(image_thumbnail_path)
        img = cv2.imread(image_thumbnail_path)
        height, width, _ = img.shape
        lower_resolution(image_thumbnail_path)
        return (img_size, width, height)
    except Exception as e:
        raise e


def find_loudest_section(audio, sr, duration):
    rms = librosa.feature.rms(y=audio).flatten()
    num_frames = len(rms)
    frames_per_chunk = int(duration * sr / 512)
    max_energy = np.argmax(
        [
            np.sum(rms[i : i + frames_per_chunk])
            for i in range(0, num_frames, frames_per_chunk)
        ]
    )
    return max_energy * 512, (max_energy * 512 + frames_per_chunk * 512)


def is_audio_valid(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        if "streams" in probe.keys() and len(probe["streams"]) > 0:
            return probe
    except ffmpeg.Error:
        pass
    return False


def audio_image(url, file_ext, savepath):
    response = requests.get(url)
    audio_data = response.content
    with tempfile.NamedTemporaryFile(suffix='.' + file_ext) as temp_file:
        temp_file.write(audio_data)
        temp_file.flush()
        desired_length = 5
        audio, sr = librosa.load(temp_file.name, sr=None, duration=desired_length)
        start, end = find_loudest_section(audio, sr, desired_length)
        extracted_audio = audio[start:end]
        fig, ax = plt.subplots(nrows=1, sharex=True, sharey=True)
        y_harm, y_perc = librosa.effects.hpss(extracted_audio)
        librosa.display.waveshow(y_harm, sr=sr, alpha=0.25, ax=ax)
        librosa.display.waveshow(y_perc, sr=sr, color="r", alpha=0.5, ax=ax)
        ax.axis("off")
        fig.patch.set_facecolor("#E2E8F0")  
        ax.set_facecolor("#E2E8F0")
        plt.savefig(
            savepath,
            bbox_inches="tight",
            pad_inches=0,
            facecolor=fig.get_facecolor(),
            edgecolor="none",
            dpi=200
        )
        plt.close()
        audio_data = is_audio_valid(temp_file.name)
    return audio_data


def bytes_to_mb(bytes_value):
    bytes_value = int(float(bytes_value))
    mb_value = bytes_value / (1024 * 1024)
    return round(mb_value, 2)

def duration_to_seconds(duration):
    hours, minutes, seconds = map(int, duration.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds
