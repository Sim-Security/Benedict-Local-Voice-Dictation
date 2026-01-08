"""
Document Editor Agent - Refines and organizes dictation documents.
Uses LangGraph to process documents with different editing styles.
"""
import os
from datetime import datetime
from typing import Annotated, TypedDict, List, Literal
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# Document editing prompts
EDIT_PROMPTS = {
    "organize": """You are a document editor. Organize and structure the following raw notes into a coherent document.

Instructions:
- Group related thoughts together
- Add clear section headers where appropriate
- Remove duplicate ideas
- Keep the original voice and meaning
- Do NOT add new content, only organize what exists
- Output ONLY the organized document, no explanations

Raw Notes:
{content}

Organized Document:""",

    "professional": """You are a professional editor. Transform these rough notes into a polished, professional document.

Instructions:
- Improve clarity and flow
- Fix grammar and punctuation
- Use professional language
- Maintain the core message and ideas
- Structure with clear sections if needed
- Output ONLY the final document, no explanations

Raw Notes:
{content}

Professional Document:""",

    "summarize": """You are a document summarizer. Create a concise summary of the following notes.

Instructions:
- Extract the key points and main ideas
- Present as a clear, readable summary
- Use bullet points for main takeaways
- Keep it under 200 words
- Output ONLY the summary, no explanations

Notes:
{content}

Summary:""",

    "action_items": """You are a task extractor. Extract all action items and to-dos from the following notes.

Instructions:
- Find all tasks, action items, and things to do
- List each as a clear, actionable item
- Include any deadlines or assignees mentioned
- Use checkbox format: - [ ] Task
- Output ONLY the action items list, no explanations

Notes:
{content}

Action Items:""",
}


class DocumentState(TypedDict):
    """State for the document editing graph."""
    content: str
    edit_mode: str
    result: str


class DocumentEditor:
    """Edits and refines dictation documents using LLM."""
    
    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or OLLAMA_MODEL
        self.base_url = base_url or OLLAMA_BASE_URL
        
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.3,
        )
        
        self.parser = StrOutputParser()
        self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph for document editing."""
        
        def edit_document(state: DocumentState) -> DocumentState:
            """Edit the document based on mode."""
            mode = state["edit_mode"]
            content = state["content"]
            
            if mode not in EDIT_PROMPTS:
                return {"result": content}
            
            prompt = ChatPromptTemplate.from_template(EDIT_PROMPTS[mode])
            chain = prompt | self.llm | self.parser
            
            result = chain.invoke({"content": content})
            return {"result": result.strip()}
        
        # Build graph
        builder = StateGraph(DocumentState)
        builder.add_node("editor", edit_document)
        builder.add_edge(START, "editor")
        builder.add_edge("editor", END)
        
        self.graph = builder.compile()
    
    def edit(self, content: str, mode: str = "organize") -> str:
        """
        Edit document content.
        
        Args:
            content: The document content to edit
            mode: Edit mode (organize, professional, summarize, action_items)
            
        Returns:
            Edited document content.
        """
        result = self.graph.invoke({
            "content": content,
            "edit_mode": mode,
            "result": ""
        })
        return result["result"]
    
    def edit_file(self, filepath: str, mode: str = "organize", 
                  output_path: str = None, backup: bool = True) -> str:
        """
        Edit a file in place or save to new location.
        
        Args:
            filepath: Path to the file to edit
            mode: Edit mode
            output_path: Optional path for output (default: overwrite original)
            backup: Whether to create a backup before editing
            
        Returns:
            Edited content string.
        """
        # Read file
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            print("File is empty, nothing to edit.")
            return ""
        
        # Create backup if requested
        if backup and not output_path:
            backup_path = f"{filepath}.backup"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📁 Backup created: {backup_path}")
        
        # Edit content
        print(f"🔄 Editing document ({mode} mode)...")
        edited = self.edit(content, mode)
        
        # Save to output path
        save_path = output_path or filepath
        with open(save_path, "w", encoding="utf-8") as f:
            # Add header with edit info
            header = f"# Document edited: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            header += f"# Edit mode: {mode}\n\n"
            f.write(header + edited)
        
        print(f"✅ Saved to: {save_path}")
        return edited
    
    @property
    def available_modes(self) -> list:
        """Return list of available edit modes."""
        return list(EDIT_PROMPTS.keys())


def main():
    """CLI for document editing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benedict Document Editor")
    parser.add_argument("file", help="Path to the file to edit")
    parser.add_argument("--mode", default="organize",
                       choices=["organize", "professional", "summarize", "action_items"],
                       help="Editing mode")
    parser.add_argument("--output", "-o", default=None,
                       help="Output file path (default: overwrite original)")
    parser.add_argument("--no-backup", action="store_true",
                       help="Don't create a backup file")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    print(f"\n📄 Document Editor")
    print(f"   File: {args.file}")
    print(f"   Mode: {args.mode}")
    print("-" * 40)
    
    editor = DocumentEditor()
    print(f"Using model: {editor.model}")
    
    result = editor.edit_file(
        args.file,
        mode=args.mode,
        output_path=args.output,
        backup=not args.no_backup
    )
    
    print("\n" + "=" * 40)
    print("Edited content preview (first 500 chars):")
    print("-" * 40)
    print(result[:500] + ("..." if len(result) > 500 else ""))


if __name__ == "__main__":
    main()
