"""
Benedict - Local Voice Dictation
Core modules for speech transcription and text processing.
"""

from .transcriber import Transcriber
from .text_processor import TextProcessor
from .session_manager import SessionManager
from .document_editor import DocumentEditor

__all__ = [
    "Transcriber",
    "TextProcessor", 
    "SessionManager",
    "DocumentEditor",
]
