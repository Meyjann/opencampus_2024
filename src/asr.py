'''
asr.py

This file contains the functionalities to recognize speech from audio files.
'''

from reazonspeech.espnet.asr import load_model, transcribe, audio_from_path
import os

model = load_model()

def recognize_speech() -> str:
    '''
    Recognizes speech from an audio file using the ReazonSpeech model.

    Returns:
        string
    '''
    audio = audio_from_path(os.path.abspath('output.wav'))

    ret = transcribe(model, audio)
    return ret.text