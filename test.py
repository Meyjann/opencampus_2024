import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer

class VideoBackground(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title and geometry
        self.setWindowTitle("Video Background")
        self.setGeometry(100, 100, 600, 1100)

        # Set the video paths
        idle_path = os.path.abspath("vtube_video/idle_vid2.mp4")
        talk_path = os.path.abspath("vtube_video/talk_vid2.mp4")
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

        # Create a QMediaPlayer to control the video playback
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.load_video()

        # Load the video file
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[self.curr_video_idx])))

        # Play the video
        self.media_player.play()

        # Create a button to start recording
        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.switch_video)
        layout.addWidget(self.record_button)

        # Widget modification
        # Make the video widget transparent
        self.video_widget.setAttribute(Qt.WA_TranslucentBackground)
        # Bring the video widget to the background
        self.video_widget.lower()

        # Create a timer to periodically update the UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)  # Update every 100 milliseconds

        # Self media st
        self.media_player.stateChanged.connect(self.handle_state_changed)
    
    def load_video(self):
        video_path = self.video_paths[self.curr_video_idx]
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.media_player.play()
    
    def run_video_from_start(self):
        self.media_player.setPosition(0)
        self.media_player.play()

    def switch_video(self):
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
    
    def handle_state_changed(self, state):
        # Restart the video if it reaches the end
        if state == QMediaPlayer.StoppedState:
            self.media_player.setPosition(0)
            self.media_player.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoBackground()
    window.show()
    sys.exit(app.exec_())
