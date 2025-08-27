import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
from audio_input import capture_audio
from audio_output import speak_text

class VoiceShell(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WachterEID Voice Shell")
        self.layout = QVBoxLayout()

        self.label = QLabel("🎙️ Speak your command:")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.listen_btn = QPushButton("🎧 Listen")
        self.listen_btn.clicked.connect(self.handle_audio)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.output)
        self.layout.addWidget(self.listen_btn)
        self.setLayout(self.layout)

    def handle_audio(self):
        transcript = capture_audio()
        self.output.append(f"🗣️ You said: {transcript}")
        response = f"Processing: {transcript}"  # Placeholder for logic routing
        speak_text(response)
        self.output.append(f"🤖 Response: {response}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    shell = VoiceShell()
    shell.show()
    sys.exit(app.exec())
