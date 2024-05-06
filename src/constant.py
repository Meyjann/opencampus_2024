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
WAVE_OUTPUT_FILENAME = "output.wav"

'''
STEN-TTS API
'''
STEN_URL = "https://ttspr.ai4med.vn/rest/tts_api_multilingual/v1"
