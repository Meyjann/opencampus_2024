import os
import requests
import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPixmap

from src import *

class AppMainWindow(QMainWindow):
    '''
    Constructor
    This section initializes the main window and all the widgets in the application.
    '''
    def __init__(self):
        super().__init__()

        # Set window title and geometry
        self.setWindowTitle("Video Background")
        self.setGeometry(100, 100, 550, 1000)

        # Set the video paths
        idle_path = os.path.abspath("./data/video/idle_vid.mov")
        talk_path = os.path.abspath("./data/video/talk_vid.mov")
        self.video_paths = [idle_path, talk_path]
        self.curr_video_idx = 0

        # Create a QWidget to hold the video widget and other widgets
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)

        # Create a layout for the central widget
        layout = QVBoxLayout()
        base_widget.setLayout(layout)

        # Create a QVideoWidget to display the video
        self.video_widget_idle = QVideoWidget()
        layout.addWidget(self.video_widget_idle)
        self.video_player_idle = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player_idle.setVideoOutput(self.video_widget_idle)

        # The second video widget for the talking video
        self.video_widget_talk = QVideoWidget()
        layout.addWidget(self.video_widget_talk)
        self.video_player_talk = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player_talk.setVideoOutput(self.video_widget_talk)

        # Load the video file
        self.video_player_idle.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[0])))
        self.video_player_idle.play()
        self.video_player_talk.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[1])))
        self.video_player_talk.play()

        # Create a QMediaPlayer to control the audio playback
        self.audio_player = QMediaPlayer()

        # Create a button to start recording
        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.handle_event_record_and_play)
        layout.addWidget(self.record_button)

        # Video widget modification
        # Make the video widget transparent
        self.video_widget_idle.setAttribute(Qt.WA_TranslucentBackground)
        self.video_widget_idle.setStyleSheet("background-color: white;")

        # Self media state changed
        self.video_player_idle.stateChanged.connect(self.handle_event_video_idle_stopped)
        self.video_player_talk.stateChanged.connect(self.handle_event_video_talk_stopped)
        self.audio_player.stateChanged.connect(self.handle_event_audio_stopped)
        self.video_widget_talk.hide()

    '''
    Event handlers
    This section contains the event handlers for the different events in the application.
    '''
    def handle_event_video_idle_stopped(self, state: QMediaPlayer.State):
        '''
        Handle the event when the idle animation video player is stopped.
        By default, the video player will be rerun.

        Parameters:
            state (int): The current state of the video player.

        Returns:
            None
        '''
        if state == QMediaPlayer.State.StoppedState:
            self.rerun_video(self.video_player_idle)

    def handle_event_video_talk_stopped(self, state: QMediaPlayer.State):
        '''
        Handle the event when the talking animation video player is stopped.
        By default, the video player will be rerun.

        Parameters:
            state (int): The current state of the video player.

        Returns:
            None
        '''
        if state == QMediaPlayer.State.StoppedState:
            self.rerun_video(self.video_player_talk)
    
    def handle_event_audio_stopped(self, state):
        '''
        Handle the event when the audio is stopped.
        By default, the idle animation will be shown and the record button will be enabled.

        Parameters:
            state (QMediaPlayer.State): The state of the audio player.

        Returns:
            None
        '''
        if state == QMediaPlayer.State.StoppedState:
            self.show_idle_animation()
        
    def handle_event_record_and_play(self):
        '''
        Handles the event to record audio, execute voice change, and play the modified audio.

        This method disables the record button, starts recording audio, executes voice change,
        fetches the modified audio file, and plays the audio while showing a talking animation.
        '''
        # Disable the record button and start recording
        self.record_button.setEnabled(False)
        print("RECORDING...")

        # Record the audio and execute voice change
        record()
        print("RECORDING DONE")
        result_url = exec_voice_change()

        # Call the API to fetch the MP3 file and play the audio
        print("PLAYING...")
        self.play_mp3_media(result_url)
        self.show_talking_animation()
    
    '''
    Utility functions
    This section contains helper functions used for various purposes in the application.
    '''
    def play_mp3_media(self, url: str):
        '''
        Downloads an MP3 file from the given URL and plays it using an audio player.

        Args:
            url (str): The URL of the MP3 file to be played.

        Returns:
            None
        '''
        response = requests.get(url)
        if response.status_code == 200:
            # Save the MP3 file locally
            with open("audio.mp3", "wb") as f:
                f.write(response.content)
            
            # Load and play the MP3 file
            self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("audio.mp3"))))
            self.audio_player.play()
        else:
            print("Failed to fetch MP3 file")
        print() # Break line
    
    def rerun_video(self, video_player: QMediaPlayer):
        '''
        Reruns the video by setting the position to the beginning and playing it.

        Parameters:
        - video_player: The video player object.

        Returns:
        None
        '''
        video_player.setPosition(0)
        video_player.play()
    
    def show_idle_animation(self):
        '''
        Hides the talking video animation and shows the idle video animation.
        Enables the record button.
        '''
        self.video_widget_talk.hide()
        self.video_widget_idle.show()
        self.record_button.setEnabled(True)
    
    def show_talking_animation(self):
        '''
        Hides the idle video animation and shows the talking video animation.
        Disables the record button.
        '''
        self.video_widget_idle.hide()
        self.video_widget_talk.show()
        self.record_button.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec_())
