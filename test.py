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
    AppMainWindow
    This class is the main window of the application. It contains the widgets (especially the video widget) to run the program.
    '''
    def __init__(self):
        '''
        Constructor
        This method initializes the application.
        '''
        super().__init__()
        # Set the audio and action queue
        self.audio_queue = []
        self.action_queue = []

        # Set the video paths
        idle_path = os.path.abspath("./data/video/idle_vid.mov")
        talk_path = os.path.abspath("./data/video/talk_vid.mov")
        self.video_paths = [idle_path, talk_path]
        
        # Initialize the used language
        self.language = "en"
        # self.language = "jp"

        # Initialize the UI
        self.init_UI()

    def init_UI(self):
        '''
        UI Constructor
        Initialize the user interface of the application.
        '''
        # Set window title and geometry
        self.setWindowTitle("Video Background")
        self.setGeometry(100, 100, 550, 835)

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
    Main functions
    This section contains the flow functions that are executed in the application.
    '''
    def talk(self):
        '''
        Play the audio file specified in the audio_file_lst.

        Parameters:
        - audio_file_lst (list[int]): A list of audio file indexes.

        Returns:
        - None
        '''
        # Check if the audio file exists. If not, do nothing
        if len(self.audio_queue) == 0:
            return
        
        # Play the audio
        audio_file = self.audio_queue[0]
        self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file)))
        self.audio_player.play()

        if self.video_widget_talk.isHidden():
            self.show_talking_animation()

    def record_and_play(self):
        '''
        Records audio, execute voice change, and play the modified audio.

        This method starts recording audio, executes voice change, then
        fetches the modified audio file, and plays the audio while showing a talking animation.
        '''
        # Disable the record button and start recording
        print("RECORDING...")

        # Record the audio and execute voice change
        record()
        print("RECORDING DONE")
        result_url = exec_voice_change()

        # Call the API to fetch the MP3 file and play the audio
        print("PLAYING...")
        self.play_mp3_media(result_url)
        self.show_talking_animation()
    
    def control_next_action(self):
        '''
        Control the next action to be executed after the current action is done.
        '''
        if len(self.action_queue) == 0:
            return
        next_action = self.action_queue[0]

        if next_action == 1:
            self.do_initial_talk()
        elif next_action == 2:
            self.record_and_play()
        elif next_action == 3:
            self.do_second_talk()
        elif next_action == 4:
            raise Exception("Unimplemented action")
        elif next_action == 5:
            self.do_final_talk()
        else:
            raise Exception("Invalid action")
        

    '''
    Event handlers
    This section contains the event handlers for the different events in the application.
    '''
    def keyPressEvent(self, event):
        '''
        Handle the keypress event.

        Parameters:
            event (QKeyEvent): The key event.

        Returns:
            None
        '''

        if event.key() == Qt.Key.Key_1:
            self.action_queue = [1, 2, 3, 5]
            self.control_next_action()
        elif event.key() == Qt.Key.Key_2:
            self.action_queue = [3, 5]
            self.control_next_action()
    
    def handle_event_video_idle_stopped(self, state: QMediaPlayer.State):
        '''
        Handle the event when the idle animation video player is stopped.
        By default, the video player will be rerun.

        Parameters:
            state (QMediaPlayer.State): The current state of the video player.

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
            state (QMediaPlayer.State): The current state of the video player.

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
            if len(self.audio_queue) > 0:
                self.audio_queue.pop(0)
                self.talk()

            if len(self.audio_queue) == 0:
                self.show_idle_animation()
                if len(self.action_queue) > 1:
                    self.action_queue.pop(0)
                    self.control_next_action()
    
    '''
    Utility functions
    This section contains helper functions used for various purposes in the application.
    '''
    def do_initial_talk(self):
        '''
        Perform initial talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"./data/audio/{self.language}/1.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/2.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/3.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/8_1.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/8_2.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/8_3.mp3"),
        ]
        self.talk()

    def do_second_talk(self):
        '''
        Perform second talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"./data/audio/{self.language}/6.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/7.mp3"),
        ]
        self.talk()

    def do_final_talk(self):
        '''
        Perform final talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"./data/audio/{self.language}/9.mp3"),
            os.path.abspath(f"./data/audio/{self.language}/10.mp3"),
        ]
        self.talk()

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
        - video_player (QMediaPlayer) : The video player object.

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
    
    def show_talking_animation(self):
        '''
        Hides the idle video animation and shows the talking video animation.
        Disables the record button.
        '''
        self.video_widget_idle.hide()
        self.video_widget_talk.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec_())
