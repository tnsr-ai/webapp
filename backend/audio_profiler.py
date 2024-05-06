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

@profile
def audio_image(url, file_ext, savepath):
    response = requests.get(url)
    audio_data = response.content
    with tempfile.NamedTemporaryFile(suffix='.' + file_ext) as temp_file:
        temp_file.write(audio_data)
        temp_file.flush()  # Ensure data is written to disk
        desired_length = 1000
        audio, sr = librosa.load(temp_file.name, sr=None, duration=desired_length)
        start, end = find_loudest_section(audio, sr, desired_length)
        extracted_audio = audio[start:end]
        fig, ax = plt.subplots(nrows=1, sharex=True, sharey=True)
        y_harm, y_perc = librosa.effects.hpss(extracted_audio)
        librosa.display.waveshow(y_harm, sr=sr, alpha=0.25, ax=ax)
        librosa.display.waveshow(y_perc, sr=sr, color="r", alpha=0.5, ax=ax)
        ax.axis("off")
        fig.patch.set_facecolor("#E2E8F0")  # set the figure background color
        ax.set_facecolor("#E2E8F0")  # set the axes element background color
        plt.savefig(
            savepath,
            bbox_inches="tight",
            pad_inches=0,
            facecolor=fig.get_facecolor(),
            edgecolor="none",
            dpi=50
        )
        plt.close()
    audio_data = is_audio_valid(temp_file.name)
    return audio_data

# Add this to the bottom of your script
if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    url = "https://aec18cb39d6670d41651478c21c17654.r2.cloudflarestorage.com/prod-content/1/song_c0a54645-ef66-4988-b16e-1100bad7dd56.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=85ae588cc54058b23c72e7bed8d94e79%2F20240424%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240424T124157Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=b6a7a19140f5cc5050d4b151c15181860d9c0044dce11fcf2a52ad5c654138f1"

    savepath = "./thumbnail/save2.png"
    audio_image(url, "jpg", savepath) 
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats()
