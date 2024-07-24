'''
main.py
This file is the main entry point for the project.
'''

import sys

from PyQt5.QtWidgets import QApplication

from src import *


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'example':
            call_stentts()
        elif sys.argv[1] == 'record':
            record()
            # result_url = exec_voice_change()
            # play_mp3_from_url(result_url)
        elif sys.argv[1] == 'backup':
            app = QApplication(sys.argv)
            window = AppMainWindowBackup()
            window.show()
            sys.exit(app.exec_())
        elif sys.argv[1] == 'exec_voice':
            # exec_voice_change()
            exec_voice_change2()
        else:
            raise Exception("Invalid command name.")
    else:
        app = QApplication(sys.argv)
        window = AppMainWindow()
        window.show()
        sys.exit(app.exec_())

