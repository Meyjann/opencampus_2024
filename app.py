import ast
import io
import json
import gradio as gr
import requests
import torch
import torchaudio
import base64

from src.constant import STEN_URL


def convert(x: torch.Tensor, text: str, lang: str) -> torch.Tensor:
    # Convert the input tensor to a base64-encoded string
    audio_binary_base64 = base64.b64encode(x.cpu().numpy().tobytes()).decode("utf-8")

    # Prepare the data for the API request
    data = {
        "text": text,
        "speed": 1.0,
        "voice": "multilingual_diff_14",
        "full_mp3": 1,
        "language": lang,
        "energy": 1.0,
        "pitch": 1.0,
        "reference": audio_binary_base64,
        "speaker_id": "",
    }

    headers = {
        "Content-type": "application/json",
    }

    # Make the API request
    response = requests.post(STEN_URL, data=json.dumps(data), headers=headers)
    data = response.json()
    url_output = data["body"]["audio_path"]

    # Download the audio file from url_output
    audio_response = requests.get(url_output)
    audio_content = audio_response.content

    # Load the audio content into a tensor
    audio_tensor, _ = torchaudio.load(io.BytesIO(audio_content))

    return audio_tensor


def process_audio(audio_file, text, language):
    # Load the audio file
    waveform, sample_rate = torchaudio.load(audio_file)

    # Convert the audio to mono if it's not already
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)

    # Convert the audio
    converted_audio = convert(waveform, text, language)

    # Save the converted audio to a file
    output_path = "converted_audio.wav"
    torchaudio.save(output_path, converted_audio, sample_rate)

    return output_path


# Sample texts
sample_texts = [
    "The quick brown fox jumps over the lazy dog.",
    "Hello, world! How are you today?",
    "Voice conversion is an exciting field of study.",
    "Artificial intelligence is transforming the way we live and work.",
    "Please select this option or type your own text below.",
]

# Language options
languages = ["chinese", "english", "indonesian", "japanese", "vietnamese"]

# Create the Gradio interface
iface = gr.Interface(
    fn=process_audio,
    inputs=[
        gr.Audio(type="filepath", label="Upload audio prompt"),
        gr.Dropdown(
            choices=sample_texts, label="Select a sample text", interactive=True
        ),
        gr.Textbox(label="Or enter your own text here"),
        gr.Dropdown(choices=languages, label="Select language", value="english"),
    ],
    outputs=gr.Audio(label="Converted Audio"),
    title="Voice Conversion Demo",
    description="Upload an audio prompt, choose or enter text, and select the text language to hear it in the style of the prompt.",
    allow_flagging="never",
)

# Launch the interface
iface.launch()
