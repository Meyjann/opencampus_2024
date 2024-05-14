'''
ui.py

This module contains the User Interface class, which is responsible for showing the user the current state of the application.
'''

import os
import requests
import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer

from .asr import recognize_speech
from .constant import *
from .voice_change import record, exec_voice_change

class AppMainWindow(QMainWindow):
    '''
    AppMainWindow
    This class is the main window of the application. It contains the widgets (especially the video widget) to run the program.
    '''
    def __init__(self, language = ""):
        '''
        Constructor
        This method initializes the application.
        '''
        super().__init__()
        # Set the audio and action queue
        self.audio_queue = []
        self.action_queue = []

        # Set the video paths
        idle_path = os.path.abspath(IDLE_VIDEO_PATH)
        talk_path = os.path.abspath(TALK_VIDEO_PATH)
        self.video_paths = [idle_path, talk_path]
        
        # Initialize the used language
        self.language = language
        if self.language == "":
            # self.language = "en"
            self.language = "jp"
        self.audio_folder = os.path.abspath(f"{AUDIO_FOLDER}/{self.language}")

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
        self.video_widget_talk.setAttribute(Qt.WA_TranslucentBackground)

        # Overlay timer
        self.timer_counter = 0

        self.overlay_timer_container = QWidget(self.video_widget_idle)
        self.overlay_timer_container.setFixedSize(120, 50)
        self.overlay_timer_container.move(self.video_widget_idle.width() // 2 - self.overlay_timer_container.width(), 0)
        # self.overlay_timer_container.setStyleSheet("background: grey")
        self.overlay_timer_container.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_timer_container.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.overlay_timer_layout = QHBoxLayout()
        self.overlay_timer_container.setLayout(self.overlay_timer_layout)

        self.recording_indicator = QLabel("REC", self.overlay_timer_container)
        self.recording_indicator.setStyleSheet("color: red; font-size: 16px; background: transparent; padding: 0px; margin: 0px;")
        self.recording_indicator.setAttribute(Qt.WA_TranslucentBackground)
        self.recording_indicator.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.recording_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.timer_label = QLabel(f"00:0{self.timer_counter}", self.overlay_timer_container)
        self.timer_label.setStyleSheet("font-size: 16px; background: transparent; padding: 0px; margin: 0 px;")
        self.timer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.timer_label.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.overlay_timer_layout.addWidget(self.recording_indicator)
        self.overlay_timer_layout.addWidget(self.timer_label)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        self.overlay_timer_container.setGraphicsEffect(self.opacity_effect)
        self.overlay_timer_container.hide()

        # Overlay transcription_text
        self.transcription_text_overlay = QLabel("Initial Transcription Text", self.video_widget_idle)
        self.transcription_text_overlay.setStyleSheet("""
            color: white;
            background-color: black;
            font-size: 20px;
            font-weight: bold;
            padding: 4px;
        """)
        self.transcription_text_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.transcription_text_overlay.setFixedWidth(530)
        self.transcription_text_overlay.setFixedHeight(50)
        self.transcription_text_overlay.move(0,760)  # Move to bottom
        self.transcription_text_overlay.hide()

        # Self media state changed
        self.video_player_idle.stateChanged.connect(self.handle_event_video_idle_stopped)
        self.video_player_talk.stateChanged.connect(self.handle_event_video_talk_stopped)
        self.audio_player.stateChanged.connect(self.handle_event_audio_stopped)
        self.video_widget_talk.hide()

        self.setStyleSheet("QWidget { background: transparent; }")

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

    def exec_recording(self):
        '''
        Records audio, execute voice change, and play the modified audio.
        Then, also writes what's being said in the audio.
        '''
        # Disable the record button and start recording
        print("RECORDING...")

        # Record the audio and execute voice change
        record()
        print("RECORDING DONE")
        result_url = exec_voice_change()
        text = recognize_speech()
        self.transcription_text_overlay.setText(text)

        # Call the API to fetch the MP3 file and play the audio
        print("PLAYING...")
        self.play_mp3_media(result_url)
        self.show_talking_animation()
        print(text)
        print()
    
    def exec_recording_animation(self):
        '''
        Executes the recording animation.
        
        This method is responsible for executing the recording animation. It performs the necessary actions to start the recording process and display the animation on the screen.
        '''
        self.timer_counter = 5

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
            self.exec_recording()
        elif next_action == 3:
            self.do_second_talk()
        elif next_action == 4:
            self.show_transcription_text()
        elif next_action == 5:
            self.do_final_talk()
        elif next_action == 6:
            self.show_recording_animation()
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
            self.action_queue = [1, 2, 3, 4, 5]
            self.control_next_action()
        elif event.key() == Qt.Key.Key_2:
            self.action_queue = [3, 5]
            self.control_next_action()
        elif event.key() == Qt.Key.Key_3:
            self.action_queue = [6]
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
    
    def handle_transcription_timer_timeout(self):
        '''
        Handle the transcription timer timeout event.
        '''
        self.transcription_text_overlay.hide()
        if len(self.action_queue) > 1:
            self.action_queue.pop(0)
            self.control_next_action()

    '''
    Utility functions
    This section contains helper functions used for various purposes in the application.
    '''
    def show_recording_animation(self):
        '''
        Show it will be recorded animation
        '''
        # Setup the fade-in animation
        self.overlay_timer_container.show()
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self.fadeIn)
        self.recording_timer.start(50)  # Adjust the interval to control the speed of the fade-in
        self.timer_opacity = 0

    def show_transcription_text(self):
        '''
        Show the transcription text overlay
        '''
        self.transcription_text_overlay.show()
        self.transcription_timer = QTimer(self)
        self.transcription_timer.timeout.connect(self.handle_transcription_timer_timeout)
        self.transcription_timer.start(3000)

    def fadeIn(self):
        '''
        Handling the fade in animation
        '''
        if self.timer_opacity >= 1:
            self.recording_timer.stop()  # Stop the timer if the maximum opacity is reached
        else:
            self.timer_opacity += 0.05  # Increase opacity
            self.opacity_effect.setOpacity(self.timer_opacity)
    
    def do_initial_talk(self):
        '''
        Perform initial talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"{self.audio_folder}/1.mp3"),
            os.path.abspath(f"{self.audio_folder}/2.mp3"),
            os.path.abspath(f"{self.audio_folder}/3.mp3"),
            os.path.abspath(f"{self.audio_folder}/8_1.mp3"),
            os.path.abspath(f"{self.audio_folder}/8_2.mp3"),
            os.path.abspath(f"{self.audio_folder}/8_3.mp3"),
        ]
        self.talk()

    def do_second_talk(self):
        '''
        Perform second talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"{self.audio_folder}/6.mp3"),
            os.path.abspath(f"{self.audio_folder}/7.mp3"),
        ]
        time.sleep(0.5)
        self.talk()

    def do_final_talk(self):
        '''
        Perform final talk by setting up audio and action queues and calling the talk method.
        '''
        self.audio_queue = [
            os.path.abspath(f"{self.audio_folder}/9.mp3"),
            os.path.abspath(f"{self.audio_folder}/10.mp3"),
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
            with open(WAVE_OUTPUT_FILENAME, "wb") as f:
                f.write(response.content)
            
            # Load and play the MP3 file
            self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(WAVE_OUTPUT_FILENAME))))
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
