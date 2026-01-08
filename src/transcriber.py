"""
Transcriber Module - Whisper STT wrapper for push-to-talk recording.
"""
import sys
import time
from typing import Callable, Optional
from RealtimeSTT import AudioToTextRecorder


class Transcriber:
    """Handles speech-to-text transcription using local Whisper."""
    
    def __init__(self, model: str = "medium.en", device: str = "cuda",
                 on_live_update: Optional[Callable[[str], None]] = None):
        """
        Initialize the transcriber.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cuda or cpu)
            on_live_update: Optional callback for real-time transcription updates
        """
        self.model = model
        self.device = device
        self.recorder = None
        self._is_recording = False
        self._transcription = ""
        self._last_displayed = ""
        self._on_live_update = on_live_update
        
    def _on_transcription(self, text: str):
        """Callback for real-time transcription updates."""
        self._transcription = text
        
        # Call external handler if provided
        if self._on_live_update:
            self._on_live_update(text)
        
    def start(self):
        """Initialize the recorder (call once at startup)."""
        print(f"Loading Whisper model '{self.model}' on {self.device}...")
        self.recorder = AudioToTextRecorder(
            model=self.model,
            language="en",
            device=self.device,
            spinner=False,
            # Increased silence duration - wait 1.5s of silence before stopping
            post_speech_silence_duration=1.5,
            # Minimum recording length to avoid premature cutoffs
            min_length_of_recording=1.0,
            # Lower sensitivity = more tolerant of pauses
            silero_sensitivity=0.2,
            webrtc_sensitivity=2,
            enable_realtime_transcription=True,
            on_realtime_transcription_update=self._on_transcription,
            realtime_processing_pause=0.1,  # Update every 100ms
            debug_mode=False,
        )
        print("Transcriber ready.")
        
    def stop(self):
        """Shutdown the recorder."""
        if self.recorder:
            self.recorder.shutdown()
            
    def record(self) -> str:
        """
        Record audio and return transcription.
        Blocks until speech is detected and silence follows.
        
        Returns:
            Transcribed text string.
        """
        if not self.recorder:
            raise RuntimeError("Transcriber not started. Call start() first.")
            
        self._transcription = ""
        self._last_displayed = ""
        text = self.recorder.text()
        return text.strip() if text else ""
    
    @property
    def live_text(self) -> str:
        """Get the current real-time transcription."""
        return self._transcription


def test_transcriber():
    """Quick test of the transcriber with live display."""
    print("Testing transcriber with live display...")
    
    def live_display(text):
        # Clear line and rewrite
        sys.stdout.write(f"\r🎤 {text}                    ")
        sys.stdout.flush()
    
    t = Transcriber(on_live_update=live_display)
    t.start()
    
    print("\nSpeak now (will transcribe until silence):")
    text = t.record()
    print(f"\n\nFinal: {text}")
    
    t.stop()
    

if __name__ == "__main__":
    test_transcriber()

