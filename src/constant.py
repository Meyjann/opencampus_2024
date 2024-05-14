'''
constant.py
This file contains all the constants used in the project.
'''

import pyaudio

'''
AUDIO FORMAT
'''
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050
CHUNK = 1024
RECORD_SECONDS = 5

AUDIO_FOLDER = "./data/audio/"
WAVE_OUTPUT_FILENAME = "output.wav"

'''
VIDEO
'''
IDLE_VIDEO_PATH = "./data/video/idle_vid.mov"
TALK_VIDEO_PATH = "./data/video/talk_vid.mov"

'''
STEN-TTS API
'''
STEN_URL = "https://ttspr.ai4med.vn/rest/tts_api_multilingual/v1"
