"""
Text Processor Module - LangChain-based text cleaning and formatting.
100% local using Ollama.
"""
import os
import sys
from typing import Generator
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Processing mode prompts
PROMPTS = {
    "clean": """You are a dictation assistant. Clean up the following speech transcription:
- Remove filler words (um, uh, like, you know, so, basically, actually)
- Fix grammar and punctuation
- Keep the original meaning and tone
- Do NOT add any extra content or explanations
- Output ONLY the cleaned text, nothing else

Transcription: {text}

Cleaned text:""",

    "rewrite": """You are a writing assistant. Rewrite the following text to be clearer and more professional:
- Improve clarity and flow
- Fix any grammar issues
- Maintain the core message
- Output ONLY the rewritten text, nothing else

Original: {text}

Rewritten:""",

    "bullets": """Convert the following text into bullet points:
- Extract key points
- Use clear, concise language
- Output ONLY the bullet points, nothing else

Text: {text}

Bullet points:""",

    "email": """Format the following as a professional email:
- Add appropriate greeting and closing
- Keep it concise and professional
- Output ONLY the email, nothing else

Content: {text}

Email:""",

    "raw": None,  # No processing, return as-is
}


class TextProcessor:
    """Processes transcribed text using local Ollama LLM."""
    
    def __init__(self, model: str = None, base_url: str = None):
        """
        Initialize the text processor.
        
        Args:
            model: Ollama model name (default from env)
            base_url: Ollama server URL (default from env)
        """
        self.model = model or OLLAMA_MODEL
        self.base_url = base_url or OLLAMA_BASE_URL
        
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.3,  # Lower temp for more consistent output
        )
        
        self.parser = StrOutputParser()
        
    def process(self, text: str, mode: str = "clean") -> str:
        """
        Process text using the specified mode (non-streaming).
        
        Args:
            text: Input text to process
            mode: Processing mode (clean, rewrite, bullets, email, raw)
            
        Returns:
            Processed text string.
        """
        if not text or not text.strip():
            return ""
            
        # Raw mode - no processing
        if mode == "raw" or mode not in PROMPTS:
            return text.strip()
            
        prompt_template = PROMPTS[mode]
        if not prompt_template:
            return text.strip()
            
        # Create chain
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | self.parser
        
        # Process
        result = chain.invoke({"text": text})
        return result.strip()
    
    def process_stream(self, text: str, mode: str = "clean") -> Generator[str, None, None]:
        """
        Process text with streaming output.
        
        Args:
            text: Input text to process
            mode: Processing mode (clean, rewrite, bullets, email, raw)
            
        Yields:
            Chunks of processed text as they are generated.
        """
        if not text or not text.strip():
            return
            
        # Raw mode - no processing, yield immediately
        if mode == "raw" or mode not in PROMPTS:
            yield text.strip()
            return
            
        prompt_template = PROMPTS[mode]
        if not prompt_template:
            yield text.strip()
            return
            
        # Create chain
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | self.parser
        
        # Stream the response
        for chunk in chain.stream({"text": text}):
            yield chunk
    
    @property
    def available_modes(self) -> list:
        """Return list of available processing modes."""
        return list(PROMPTS.keys())


def test_processor():
    """Quick test of the text processor with streaming."""
    print(f"Testing text processor with model: {OLLAMA_MODEL}")
    
    processor = TextProcessor()
    
    test_text = "um so like I was thinking we should probably maybe have a meeting tomorrow you know to discuss the project"
    
    print(f"\nOriginal: {test_text}")
    print(f"\nStreaming output: ", end="", flush=True)
    
    for chunk in processor.process_stream(test_text, 'clean'):
        print(chunk, end="", flush=True)
    print()  # newline at end


if __name__ == "__main__":
    test_processor()

