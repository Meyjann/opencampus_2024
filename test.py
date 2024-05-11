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

class VideoBackground(QMainWindow):
    '''
    Constructor
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
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a layout for the central widget
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create a QVideoWidget to display the video
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player.setVideoOutput(self.video_widget)

        # The second video widget for the talking video
        self.video_widget_run = QVideoWidget()
        layout.addWidget(self.video_widget_run)
        self.video_player_run = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player_run.setVideoOutput(self.video_widget_run)

        # Load the video file
        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[0])))
        self.video_player.play()
        self.video_player_run.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[1])))
        self.video_player_run.play()

        # Create a QMediaPlayer to control the audio playback
        self.audio_player = QMediaPlayer()

        # Create a button to start recording
        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.record_and_play)
        layout.addWidget(self.record_button)

        # Video widget modification
        # Make the video widget transparent
        self.video_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.video_widget.setStyleSheet("background-color: white;")

        # Create a timer to periodically update the UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)  # Update every 100 milliseconds

        # Self media state changed
        self.video_player.stateChanged.connect(self.handle_video_state_changed)
        self.video_player_run.stateChanged.connect(self.handle_video_run_state_changed)
        self.audio_player.stateChanged.connect(self.handle_audio_state_changed)
        self.video_widget_run.hide()

    '''
    Event handlers
    '''
    def handle_video_state_changed(self, state):
        # Restart the video if it reaches the end
        if state == QMediaPlayer.StoppedState:
            self.video_player.setPosition(0)
            self.video_player.play()

    def handle_video_run_state_changed(self, state):
        # Restart the video if it reaches the end
        if state == QMediaPlayer.StoppedState:
            self.video_player_run.setPosition(0)
            self.video_player_run.play()
    
    def handle_audio_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.video_widget_run.hide()
            self.video_widget.show()
            self.record_button.setEnabled(True)
        
    def record_and_play(self):
        # Call the API to fetch the MP3 file from the online URL
        self.record_button.setEnabled(False)
        print("RECORDING...")
        record()
        print("RECORDING DONE")
        result_url = exec_voice_change()
        print("PLAYING...")
        
        self.play_mp3_media(result_url)
        self.video_widget.hide()
        self.video_widget_run.show()

    def handle_video_loaded(self, state):
        if state == QMediaPlayer.LoadedMedia:
            # Video is loaded, disconnect the signal and start playing
            self.video_player.stateChanged.disconnect(self.handle_video_loaded)
            self.video_player.play()
    
    '''
    Utility functions
    '''
    def play_mp3_media(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            # Save the MP3 file locally
            with open("audio.mp3", "wb") as f:
                f.write(response.content)
            
            # Load and play the MP3 file
            self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("audio.mp3"))))
            print("Playing MP3 file")
            self.audio_player.play()
        else:
            print("Failed to fetch MP3 file")
        print()
        
    def switch_video(self, change_idx = True):
        if change_idx:
            if self.curr_video_idx == 0:
                self.curr_video_idx = 1
            else:
                self.curr_video_idx = 0
        self.load_video()

    def update_ui(self):
        # Update the button state based on the video playback status
        if self.curr_video_idx == 1:
            self.record_button.setEnabled(False)
        else:
            self.record_button.setEnabled(True)
    
    def load_video(self):
        # self.video_player.stop()
        video_path = self.video_paths[self.curr_video_idx]
        self.idle_image_label.show()

        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.video_player.play()

        self.video_player.stateChanged.connect(self.handle_video_loaded)
        self.idle_image_label.hide()
        self.video_widget.lower()        
    
    def run_video_from_start(self):
        self.video_player.setPosition(0)
        self.video_player.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoBackground()
    window.show()
    sys.exit(app.exec_())
