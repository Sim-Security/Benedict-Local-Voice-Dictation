"""
Benedict - Local Voice Dictation App
=====================================
Hold a hotkey, speak, release - clean text appears.
100% local using Whisper + Ollama.

Usage:
    python main.py [--mode MODE] [--hotkey KEY]

Modes: clean, rewrite, bullets, email, raw
"""
import os
import sys
import time
import argparse
from datetime import datetime
import pyperclip
import keyboard
from dotenv import load_dotenv

from src.transcriber import Transcriber
from src.text_processor import TextProcessor
from src.session_manager import SessionManager

load_dotenv()

# Configuration
DEFAULT_HOTKEY = os.getenv("DICTATION_HOTKEY", "ctrl")
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "clean")


def print_banner():
    """Print startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  BENEDICT - Local Voice Dictation                            ║
║  Hold [HOTKEY] → Speak → Release → Clean text appears        ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="Benedict Voice Dictation")
    parser.add_argument("--mode", default=DEFAULT_MODE, 
                       choices=["clean", "rewrite", "bullets", "email", "raw"],
                       help="Text processing mode")
    parser.add_argument("--hotkey", default=DEFAULT_HOTKEY,
                       help="Hotkey to hold while speaking (default: ctrl)")
    parser.add_argument("--no-copy", action="store_true",
                       help="Disable copying to clipboard")
    parser.add_argument("--no-session", action="store_true",
                       help="Disable automatic session document creation")
    args = parser.parse_args()
    
    print_banner()
    print(f"Mode: {args.mode}")
    print(f"Hotkey: Hold [{args.hotkey.upper()}] to record")
    if not args.no_copy:
        print("Copy to clipboard: Yes")
    print("-" * 60)
    
    # Live transcription display callback
    def live_display(text):
        """Display transcription in real-time, overwriting the line."""
        display_text = text[:80] + "..." if len(text) > 80 else text
        sys.stdout.write(f"\r🎤 {display_text:<85}")
        sys.stdout.flush()
    
    # Initialize components
    print("\nInitializing...")
    transcriber = Transcriber(on_live_update=live_display)
    transcriber.start()
    
    processor = TextProcessor()
    print(f"Using Ollama model: {processor.model}")
    
    # Initialize session manager (creates document automatically)
    session = None
    if not args.no_session:
        session = SessionManager()
    
    print("\n" + "=" * 60)
    print("Ready! Hold the hotkey and speak. Press CTRL+C to exit.")
    print("=" * 60 + "\n")
    
    try:
        while True:
            # Wait for hotkey press
            keyboard.wait(args.hotkey)
            print(f"\n🎤 Recording... (release [{args.hotkey.upper()}] when done)")
            
            # Record until hotkey released
            start_time = time.time()
            raw_text = transcriber.record()
            elapsed = time.time() - start_time
            
            if not raw_text:
                print("\r" + " " * 90 + "\r   (No speech detected)")
                continue
            
            # Clear the live transcription line
            print("\r" + " " * 90)
            print(f"📝 Raw ({elapsed:.1f}s): {raw_text}")
            
            # Process the text (with streaming for live output)
            if args.mode != "raw":
                print(f"🔄 Processing ({args.mode})... ", end="", flush=True)
                print("\n✅ Result: ", end="", flush=True)
                
                processed_text = ""
                for chunk in processor.process_stream(raw_text, args.mode):
                    print(chunk, end="", flush=True)
                    processed_text += chunk
                print()
            else:
                processed_text = raw_text
                print(f"\n✅ Result:\n{processed_text}")
            
            # Add to session document
            if session:
                session.add_transcription(raw_text, processed_text)
            
            # Copy to clipboard
            if not args.no_copy:
                pyperclip.copy(processed_text)
                print("📋 Copied to clipboard!")
                
            print("\n" + "-" * 40)
            
    except KeyboardInterrupt:
        print("\n\nFinalizing session...")
    finally:
        # Finalize session with organized summary
        if session:
            session.finalize(organize=True)
        transcriber.stop()
        print("Goodbye!")


if __name__ == "__main__":
    main()
