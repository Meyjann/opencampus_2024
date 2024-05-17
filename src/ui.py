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
from .ui_background import *

def merge_task():
    print("All tasks have been completed")

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

        # Set the audio, action queue, and task counter
        self.audio_queue = []
        self.action_queue = []
        self.tasks_completed = 0

        self.recognized_text = ""
        self.result_url = ""

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
        self.audio_player_2 = QMediaPlayer()

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
        self.overlay_timer_container.setFixedWidth(200)

        self.overlay_timer_layout = QHBoxLayout()
        self.overlay_timer_container.setLayout(self.overlay_timer_layout)

        self.recording_indicator = QLabel("RECORDING", self.overlay_timer_container)
        self.recording_indicator.setStyleSheet("color: red; font-size: 16px; background: transparent; padding: 0px; margin: 0px;")
        self.recording_indicator.setAttribute(Qt.WA_TranslucentBackground)
        self.recording_indicator.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.recording_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.recording_indicator.setFixedWidth(100)

        self.timer_label = QLabel(f"00:0{self.timer_counter}", self.overlay_timer_container)
        self.timer_label.setStyleSheet("font-size: 20px; background: transparent; padding: 0px; margin: 0 px;")
        self.timer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.timer_label.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.overlay_timer_layout.addWidget(self.recording_indicator)
        self.overlay_timer_layout.addWidget(self.timer_label)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(1)
        self.overlay_timer_container.setGraphicsEffect(self.opacity_effect)
        self.overlay_timer_container.hide()

        # Overlay transcription_text
        self.transcription_text_overlay = QLabel("Initial Transcription Text", self.video_widget_idle)
        self.transcription_text_overlay.setStyleSheet("""
            color: white;
            background-color: black;
            font-size: 24px;
            font-weight: bold;
            padding: 4px;
        """)
        self.transcription_text_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.transcription_text_overlay.setFixedWidth(self.width())
        self.transcription_text_overlay.setFixedHeight(50)
        self.transcription_text_overlay.move(0,self.height() - self.transcription_text_overlay.height())  # Move to bottom
        self.transcription_text_overlay.hide()

        # Self media state changed
        self.video_player_idle.stateChanged.connect(self.handle_event_video_idle_stopped)
        self.video_player_talk.stateChanged.connect(self.handle_event_video_talk_stopped)
        self.audio_player.stateChanged.connect(self.handle_event_audio_stopped)
        self.audio_player_2.stateChanged.connect(self.handle_event_audio_stopped_2)
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
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_timer_container.move(self.video_widget_idle.width() - self.overlay_timer_container.width(), self.video_widget_idle.height() // 2 - self.overlay_timer_container.height() // 2)
        self.transcription_text_overlay.setFixedWidth(self.width())
        self.transcription_text_overlay.move(0,self.video_widget_idle.height() - self.transcription_text_overlay.height() - self.video_widget_idle.height() // 2 - self.video_widget_idle.height() // 8)  # Move to bottom

    def exec_recording(self):
        '''
        Records audio and saves the recorded audio
        '''
        # Initialize job thread
        self.background_task1 = TaskRecordAudio()
        self.background_thread1 = QThread()
        self.background_task1.moveToThread(self.background_thread1)

        self.background_thread1.started.connect(self.background_task1.run)
        self.background_task1.signal.connect(self.recording_manager)
        self.background_task1.signal.connect(self.background_thread1.quit)

        print("RECORDING...") 
        self.background_thread1.start()
        self.show_recording_animation()

    def do_tts_and_asr(self):
        '''
        Executes voice change and speech recognition
        Saves the modifed audio
        '''
        # Initialize job thread for synthesizing audio
        self.background_task2 = TaskFetchSynthesizedAudio(task_num = 1)
        self.background_thread2 = QThread()
        self.background_task2.moveToThread(self.background_thread2)

        self.background_thread2.started.connect(self.background_task2.run)
        self.background_task2.signal.connect(self.ai_process_manager)
        self.background_task2.signal.connect(self.background_thread2.quit)

        # Initialize job thread for transcription
        self.background_task3 = TaskGenerateAudioTranscription(task_num = 2)
        self.background_thread3 = QThread()
        self.background_task3.moveToThread(self.background_thread3)

        self.background_thread3.started.connect(self.background_task3.run)
        self.background_task3.signal.connect(self.ai_process_manager)
        self.background_task3.signal.connect(self.background_thread3.quit)

        # Executing all jobs at the same time
        print("TRANSCRIPTING AND GENERATING SPEECH...")
        self.background_thread2.start()
        self.background_thread3.start()

        audio_file = os.path.abspath(f"{self.audio_folder}/4.mp3")
        self.audio_player_2.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file)))
        self.audio_player_2.play()
        self.show_talking_animation()

        # self.result_url = exec_voice_change()
        # self.recognized_text = recognize_speech()
        # self.play_modified_audio()


    def play_modified_audio(self):
        '''
        Play the saved modified audio
        '''
        # Call the API to fetch the MP3 file and play the audio
        print("PLAYING...")
        # self.play_mp3_media(self.result_url)
        self.play_mp3_media_2()
        self.show_talking_animation()
        print(self.recognized_text)
        print()

    def control_next_action(self):
        '''
        Control the next action to be executed after the current action is done.
        '''
        print(self.action_queue)
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
        if len(self.action_queue) > 0:
            return
        if event.key() == Qt.Key.Key_1:
            self.action_queue = [1, 2, 3, 4, 5]
            print("CALL 1")
            self.control_next_action()
        elif event.key() == Qt.Key.Key_2:
            self.action_queue = [3, 5]
            print("CALL 2")
            self.control_next_action()
        elif event.key() == Qt.Key.Key_3:
            self.action_queue = [6]
            print("CALL 3")
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
                    print("CALL 4")
                    self.control_next_action()
                else:
                    self.action_queue = []

    def handle_event_audio_stopped_2(self, state):
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
            self.ai_process_manager(True, "Successful audio rendering", 0)
    
    def handle_transcription_timer_timeout(self):
        '''
        Handle the transcription timer timeout event.
        '''
        self.transcription_text_overlay.hide()
        if len(self.action_queue) > 1:
            self.action_queue.pop(0)
            print("CALL 5")
            self.control_next_action()
        else:
            self.action_queue = []

    '''
    Utility functions
    This section contains helper functions used for various purposes in the application.
    '''
    def show_recording_animation(self):
        '''
        Show it will be recorded animation
        '''
        self.timer_counter = 0
        self.blink_counter = 0
        self.timer_opacity = 0
        self.opacity_effect.setOpacity(self.timer_opacity)

        # Setup the fade-in animation3
        self.timer_label.setText(f"00:0{self.timer_counter}")
        self.overlay_timer_container.show()
        self.recording_indicator.setVisible(True)
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self.fadeIn)
        self.recording_timer.start(10)  # Adjust the interval to control the speed of the fade-in

    def show_transcription_text(self):
        '''
        Show the transcription text overlay
        '''
        self.transcription_text_overlay.show()
        self.transcription_timer = QTimer(self)
        self.transcription_timer.setSingleShot(True)
        self.transcription_timer.timeout.connect(self.handle_transcription_timer_timeout)
        self.transcription_timer.start(3000)

    def fadeIn(self):
        '''
        Handling the fade in animation
        '''
        if self.timer_opacity >= 1:
            self.recording_timer.stop()  # Stop the timer if the maximum opacity is reached
            self.blink_recording()
        else:
            self.timer_opacity += 0.1  # Increase opacity
            self.opacity_effect.setOpacity(self.timer_opacity)
    
    def blink_recording(self):
        '''
        This section handles the animation for blinking in the recording
        '''
        self.timer_counter = 0
        self.blink_counter = 0
        self.recording_timer.start(BLINK_MS)
        self.recording_timer.timeout.connect(self.blink)

    def blink(self):
        '''
        This is the basic function called during the blink timeout
        '''
        self.blink_counter += BLINK_MS
        timer_counter = 0
        timer_counter += self.blink_counter // 1000
        if timer_counter != self.timer_counter:
            self.timer_counter = timer_counter
            self.timer_label.setText(f"00:0{self.timer_counter}")
        if self.timer_counter < RECORD_SECONDS:
            self.recording_indicator.isVisible = not self.recording_indicator.isVisible
            self.recording_indicator.setVisible(self.recording_indicator.isVisible)
        else:
            self.recording_timer.stop()
            self.recording_timer.timeout.connect(self.fadeIn)
            self.overlay_timer_container.hide()
            self.recording_manager(True, "Successful recording animation", 0)

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
            os.path.abspath(f"{self.audio_folder}/8_4.mp3"),
        ]
        print(self.audio_queue)
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

    def play_mp3_media_2(self):
        '''
        Downloads an MP3 file from the given URL and plays it using an audio player.

        Args:
            url (str): The URL of the MP3 file to be played.

        Returns:
            None
        '''
        self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(WAVE_OUTPUT_FILENAME))))
        self.audio_player.play()
    
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
    
    def recording_manager(self, success: bool, message: str, task_num: int = 0):
        '''
        Manages when the recording task is finished
        '''
        self.tasks_completed += 1
        if self.tasks_completed == 2: # Both the recording and the UI animation
            self.tasks_completed = 0
            self.do_tts_and_asr()

    def ai_process_manager(self, success: bool, message: str, task_num: int = 0):
        '''
        Manages when the process task is finished
        '''
        if not success:
            raise Exception("Unimplmented case when there is failure when synthesis and transcription")

        if task_num == 2:
            self.recognized_text = message
            self.transcription_text_overlay.setText(self.recognized_text)
            print(self.recognized_text)

        self.tasks_completed += 1
        if self.tasks_completed == 3: # Synthesis, transcription and the UI recording
            self.tasks_completed = 0
            self.play_modified_audio()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec_())
