import requests
import json
import base64
import ast

url = "http://163.221.176.238:9874/rest/tts_api_multilingual/v1"

filename = "output.wav"
audio_binary = open(filename, 'rb') #open binary file in read mode
audio_binary_base64 = base64.b64encode(audio_binary.read())

text = "このデモはHAI研究室の音声合成技術を使用しています。"

code_lang = "japanese"
if code_lang == "english":
    text = "This speech was generated using STEN T.T.S. from H.A.I. Lab."

data = {
    'text': text,
    'speed': 1.0,
    'voice': 'multilingual_diff_14',
    'full_mp3': 1,
    'language': code_lang,
    'energy': 1.0,
    'pitch': 1.0,
    'reference': audio_binary_base64.decode('utf-8'),
    'speaker_id': ''
}

print(data)

headers = {
    'Content-type': 'application/json',
}

response = requests.post(url, data=json.dumps(data), headers=headers)
data = response.content
data = ast.literal_eval(data.decode("utf-8"))
url_output = data["body"]["audio_path"]

print(url_output)