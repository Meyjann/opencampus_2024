import ast
import base64
import json
import pyaudio
import requests
import wave
import sounddevice as sd
import numpy as np

from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
from scipy.io.wavfile import write


from src import *


def record(filename: str = WAVE_OUTPUT_FILENAME):
    '''
    Records audio from the default input device and saves it to a WAV file.

    Args:
        filename (str): The name of the WAV file to save the recorded audio. Defaults to WAVE_OUTPUT_FILENAME.

    Returns:
        None
    '''
    # Define the duration of the recording in seconds and the sample rate
    duration = 5  # seconds
    sample_rate = 22050  # Hz

    # Record audio
    print("Recording...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    print("Recording finished.")

    # Normalize to 16-bit range
    audio_normalized = np.int16(audio / np.max(np.abs(audio)) * 32767)

    # Save the recording into a WAV file
    write(filename, sample_rate, audio_normalized)
    print(f"File saved as {filename}.")

def play_audio(filename: str = WAVE_OUTPUT_FILENAME):
    '''
    Play the recorded audio from the specified file.

    Args:
        filename (str): The path to the audio file to be played.

    Returns:
        None
    '''
    # Play the recorded audio
    wave_file = wave.open(filename, 'rb')

    audio = pyaudio.PyAudio()

    stream = audio.open(format=audio.get_format_from_width(wave_file.getsampwidth()),
                        channels=wave_file.getnchannels(),
                        rate=wave_file.getframerate(),
                        output=True)

    print("Playing recorded audio...")

    data = wave_file.readframes(CHUNK)

    while data:
        stream.write(data)
        data = wave_file.readframes(CHUNK)

    print("Playback finished.")

    # Stop playing
    stream.stop_stream()
    stream.close()
    audio.terminate()

def sten_tts(source_filename: str = WAVE_OUTPUT_FILENAME, target_filename: str = WAVE_OUTPUT_FILENAME):
    '''
    Perform text-to-speech using the STEN TTS API.

    Args:
        source_filename (str): The path to the source file name
        target_filename (str): The path to the result file name
    '''
    audio_binary = open(source_filename, 'rb') #open binary file in read mode
    audio_binary_base64 = base64.b64encode(audio_binary.read())
    text = "これは北陸先端科学技術大学院大学"

    data = {
        'text': text,
        'speed': 1.0,
        'voice': 'multilingual_diff_14',
        'full_mp3': 1,
        'language': "japanese",
        'energy': 1.0,
        'pitch': 1.0,
        'reference': audio_binary_base64.decode('utf-8'),
        'speaker_id': ''
    }

    headers = {
        'Content-type': 'application/json',
    }

    response = requests.post(URL, data=json.dumps(data), headers=headers)
    data = response.content
    data = ast.literal_eval(data.decode("utf-8"))
    url_output = data["body"]["audio_path"]

    print(url_output)

    play_mp3_from_url(url_output)

def play_mp3_from_url(url: str):
    '''
    Play an MP3 audio file from a URL.

    Args:
        url (str): The URL of the MP3 file to be played.

    Returns:
        None
    '''
    response = requests.get(url)

    if response.status_code == 200:
        audio_data = BytesIO(response.content)
        audio = AudioSegment.from_file(audio_data, format='mp3')

        play(audio)
    else:
        print("Faild to get audio data from URL.")


if __name__ == '__main__':
    
    record()
    sten_tts()
    # sten_tts('./reference_audio/439.wav', './output.wav')
    # play_mp3_from_url('https://ttspr.ai4med.vn/synthesis/112300_0_1_1714643163355.mp3')
