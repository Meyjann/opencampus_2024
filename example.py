#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Import the json library
import json
import requests
import urllib
import pdb
import ast
import base64

url = "https://ttspr.ai4med.vn/rest/tts_api_multilingual/v1"

filename = "./reference_audio/439.wav"
audio_binary = open(filename, 'rb') #open binary file in read mode
audio_binary_base64 = base64.b64encode(audio_binary.read())

language = ["english", "japanese"]
texts = [
    "this is the system developed by the research team of the japan advanced institute of science and technology",
    "これは北陸先端科学技術大学院大学の研究チームが開発したシステムです",
]

for index, (text, lang) in enumerate(zip(texts, language)):
    data = {
            'text': text,
            'speed': 1.0,
            'voice': 'multilingual_diff_14',
            'full_mp3': 1,
            'language': lang,
            'energy': 1.0,
            'pitch': 1.0,
            'reference': audio_binary_base64.decode('utf-8'),
            'speaker_id': ''
        }

    headers = {
            'Content-type': 'application/json',
        }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    data = response.content
    data = ast.literal_eval(data.decode("utf-8"))
    print(data["body"]["audio_path"])
