'''
ui_background.py

This file manages the background threads for the UI.
'''

from PyQt5.QtCore import QThread, pyqtSignal as Signal, QObject

import requests

from .asr import recognize_speech
from .constant import WAVE_OUTPUT_FILENAME
from .voice_change import record, exec_voice_change


def fetch_synthesized_audio():
    '''
    Mimic the voice of the user.
    '''
    url = exec_voice_change()
    response = requests.get(url)
    if response.status_code == 200:
        with open(WAVE_OUTPUT_FILENAME, "wb") as f:
            f.write(response.content)
    else:
        raise Exception("Failed to fetch synthesized audio.")


class BackgroundWorker(QObject):
    '''
    A class to manage background threads for the UI.

    Attributes:
        function (function): The function to run in the background thread.
        args (list): The arguments to pass to the function.
    '''
    signal = Signal(bool, str)

    def __init__(self, target_function, args: list):
        '''
        Initializes the BackgroundThreadWithArgs class.

        Args:
            function (function): The function to run in the background thread.
            args (list): The arguments to pass to the function.
        '''
        super().__init__()
        self.function = target_function
        self.args = args

    def run(self):
        '''
        Runs the function in the background thread.
        '''
        try:
            response = self.function(*self.args)
            self.signal.emit(True, response)
        except Exception as e:
            self.signal.emit(False, e)


class TaskRecordAudio(BackgroundWorker):
    '''
    A class to manage background threads when recording audio for the UI.

    Attributes:
        function (function): The function to run in the background thread.
        args (list): The arguments to pass to the function.
    '''
    def __init__(self):
        '''
        Initializes the BackgroundThreadWithArgs class.

        Args:
            function (function): The function to run in the background thread.
            args (list): The arguments to pass to the function.
        '''
        function = record
        args = []
        super().__init__(function, args)

class TaskFetchSynthesizedAudio(BackgroundWorker):
    '''
    A class to manage background threads when fetching synthesized audio for the UI.

    Attributes:
        function (function): The function to run in the background thread.
        args (list): The arguments to pass to the function.
    '''
    def __init__(self, audio_url = str):
        '''
        Initializes the BackgroundThreadWithArgs class.

        Args:
            function (function): The function to run in the background thread.
            args (list): The arguments to pass to the function.
        '''
        function = fetch_synthesized_audio
        args = [audio_url]
        super().__init__(function, args)


class TaskGenerateAudioTranscription(BackgroundWorker):
    '''
    A class to manage background threads when generating audio transcription for the UI.

    Attributes:
        function (function): The function to run in the background thread.
        args (list): The arguments to pass to the function.
    '''
    def __init__(self):
        '''
        Initializes the BackgroundThreadWithArgs class.

        Args:
            function (function): The function to run in the background thread.
            args (list): The arguments to pass to the function.
        '''
        function = recognize_speech
        args = []
        super().__init__(function, args)