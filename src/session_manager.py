"""
Session Manager - Manages dictation sessions with auto-document creation.
Creates timestamped documents with auto-generated titles and organized sections.
"""
import os
import re
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "sessions")


class SessionManager:
    """Manages a dictation session with automatic document creation."""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.session_start = datetime.now()
        self.transcriptions = []
        self.title = "Untitled Session"
        self.filepath = None
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize LLM for title generation
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
        )
        self.parser = StrOutputParser()
        
        # Create initial file
        self._create_session_file()
        
    def _create_session_file(self):
        """Create the session file with initial structure."""
        timestamp = self.session_start.strftime("%Y-%m-%d_%H-%M")
        filename = f"{timestamp}_session.md"
        self.filepath = os.path.join(self.output_dir, filename)
        
        header = f"""# {self.title}

**Session Started:** {self.session_start.strftime("%Y-%m-%d %H:%M")}

---

## Raw Transcription

"""
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(header)
            
        print(f"📄 Created session: {self.filepath}")
        
    def add_transcription(self, text: str, cleaned_text: str = None):
        """Add a transcription to the session."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = cleaned_text or text
        
        self.transcriptions.append({
            "time": timestamp,
            "raw": text,
            "cleaned": cleaned_text or text
        })
        
        # Append to file
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(f"**[{timestamp}]** {entry}\n\n")
        
        # Generate title from first transcription
        if len(self.transcriptions) == 1:
            self._generate_title(entry)
            
    def _generate_title(self, first_text: str):
        """Generate a descriptive title from the first transcription."""
        prompt = ChatPromptTemplate.from_template(
            """Generate a short, descriptive title (3-6 words) for a document that starts with:
"{text}"

Output ONLY the title, nothing else. No quotes, no punctuation at the end.

Title:"""
        )
        
        chain = prompt | self.llm | self.parser
        
        try:
            self.title = chain.invoke({"text": first_text[:200]}).strip()
            # Clean up the title
            self.title = re.sub(r'[^\w\s-]', '', self.title)[:50]
            self._update_file_title()
            print(f"📝 Session title: {self.title}")
        except Exception as e:
            print(f"(Could not generate title: {e})")
            
    def _update_file_title(self):
        """Update the title in the file and rename the file."""
        # Read current content
        with open(self.filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace title
        content = re.sub(r'^# .+$', f'# {self.title}', content, count=1, flags=re.MULTILINE)
        
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Rename file to include title
        timestamp = self.session_start.strftime("%Y-%m-%d_%H-%M")
        safe_title = re.sub(r'[^\w\s-]', '', self.title).replace(' ', '_')[:30]
        new_filename = f"{timestamp}_{safe_title}.md"
        new_filepath = os.path.join(self.output_dir, new_filename)
        
        try:
            os.rename(self.filepath, new_filepath)
            self.filepath = new_filepath
        except Exception:
            pass  # Keep original name if rename fails
            
    def finalize(self, organize: bool = True):
        """Finalize the session and optionally add organized section."""
        if not self.transcriptions:
            print("No transcriptions to finalize.")
            return
            
        # Combine all cleaned transcriptions
        all_text = "\n".join([t["cleaned"] for t in self.transcriptions])
        
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write("\n---\n\n## Organized Summary\n\n")
            
            if organize:
                # Use LLM to organize
                prompt = ChatPromptTemplate.from_template(
                    """Organize and structure the following notes into a clear, readable document.
- Group related ideas together
- Add section headers if appropriate
- Remove redundancy
- Keep the original voice

Notes:
{text}

Organized document:"""
                )
                
                chain = prompt | self.llm | self.parser
                
                print("🔄 Organizing session content...")
                try:
                    organized = chain.invoke({"text": all_text})
                    f.write(organized.strip())
                except Exception as e:
                    f.write(f"(Organization failed: {e})\n\n{all_text}")
            else:
                f.write(all_text)
                
            f.write(f"\n\n---\n\n*Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        print(f"✅ Session finalized: {self.filepath}")
        return self.filepath


def test_session():
    """Test the session manager."""
    session = SessionManager()
    
    session.add_transcription(
        "um so I was thinking about the project timeline",
        "I was thinking about the project timeline"
    )
    session.add_transcription(
        "we need to hire more developers",
        "We need to hire more developers."
    )
    
    session.finalize()


if __name__ == "__main__":
    test_session()
