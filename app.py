"""
Benedict - Streamlit Web Frontend
================================
A web UI for browsing sessions, recording dictations, and editing documents.
"""
import os
import glob
import threading
import streamlit as st
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.document_editor import DocumentEditor
from src.text_processor import TextProcessor
from src.session_manager import SessionManager

# Configuration
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Page config
st.set_page_config(
    page_title="Benedict - Voice Dictation",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .record-btn {
        background: linear-gradient(90deg, #f43f5e 0%, #ec4899 100%);
        color: white;
        font-size: 1.2rem;
        padding: 1rem 2rem;
        border-radius: 50px;
    }
    .stTextArea textarea {
        font-family: 'Monaco', 'Consolas', monospace;
    }
</style>
""", unsafe_allow_html=True)


def get_sessions():
    """Get all session files sorted by date."""
    pattern = os.path.join(SESSIONS_DIR, "*.md")
    files = glob.glob(pattern)
    sessions = []
    for f in files:
        stat = os.stat(f)
        sessions.append({
            "path": f,
            "name": os.path.basename(f),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "size": stat.st_size
        })
    return sorted(sessions, key=lambda x: x["modified"], reverse=True)


def read_session(path):
    """Read session content."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_session(path, content):
    """Save session content."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    # Header
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown('<p class="main-header">🎤 Benedict</p>', unsafe_allow_html=True)
        st.caption("Local Voice Dictation • 100% Private")
    with col_header2:
        # New Session button
        if st.button("➕ New Session", type="primary", use_container_width=True):
            st.session_state.show_new_session = True
            if "selected_session" in st.session_state:
                del st.session_state.selected_session
    
    sessions = get_sessions()
    
    # Sidebar - Session Browser
    with st.sidebar:
        st.header("📁 Sessions")
        
        if not sessions:
            st.info("No sessions yet. Create one above!")
        else:
            st.caption(f"{len(sessions)} session(s)")
            
            for i, session in enumerate(sessions):
                name = session["name"].replace(".md", "")
                parts = name.split("_", 2)
                if len(parts) >= 3:
                    date_str = parts[0]
                    title = parts[2].replace("_", " ")
                else:
                    date_str = session["modified"].strftime("%Y-%m-%d")
                    title = name
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📄 {title[:25]}...", key=f"session_{i}", use_container_width=True):
                        st.session_state.selected_session = session["path"]
                        st.session_state.edit_mode = False
                        if "show_new_session" in st.session_state:
                            del st.session_state.show_new_session
                with col2:
                    st.caption(date_str)
        
        st.divider()
        
        # Quick Actions
        st.header("⚡ Actions")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Main Content
    if st.session_state.get("show_new_session"):
        # New Session / Quick Dictation Mode
        st.markdown("---")
        st.subheader("📝 New Session")
        
        # Mode selector
        mode = st.selectbox(
            "Processing Mode",
            ["clean", "rewrite", "bullets", "email", "raw"],
            help="How to process your dictation"
        )
        
        # Text input area
        st.markdown("**Enter or paste your text:**")
        input_text = st.text_area(
            "Input",
            height=200,
            placeholder="Type or paste text here, or use 'python main.py' for voice input...",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Process Text", type="primary", use_container_width=True):
                if input_text.strip():
                    with st.spinner(f"Processing ({mode})..."):
                        processor = TextProcessor()
                        processed = processor.process(input_text, mode)
                        st.session_state.processed_text = processed
                        st.session_state.raw_text = input_text
        with col2:
            if st.button("💾 Save as Session", use_container_width=True):
                if input_text.strip() or st.session_state.get("processed_text"):
                    session = SessionManager()
                    raw = st.session_state.get("raw_text", input_text)
                    processed = st.session_state.get("processed_text", input_text)
                    session.add_transcription(raw, processed)
                    session.finalize(organize=False)
                    st.success(f"Saved to {session.filepath}")
                    st.session_state.selected_session = session.filepath
                    del st.session_state.show_new_session
                    st.rerun()
        
        # Show processed result
        if "processed_text" in st.session_state:
            st.markdown("---")
            st.subheader("✅ Processed Result")
            st.markdown(st.session_state.processed_text)
            
            if st.button("📋 Copy to Clipboard"):
                st.code(st.session_state.processed_text)
                st.info("👆 Select and copy the text above (Ctrl+C)")
        
        # Voice instructions
        st.markdown("---")
        with st.expander("🎤 Voice Recording (CLI)"):
            st.markdown("""
            For voice dictation, run in terminal:
            ```bash
            python main.py
            ```
            Hold **CTRL** → Speak → Release → Text appears here after refresh.
            """)
    
    elif "selected_session" not in st.session_state:
        # Welcome screen
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎤 Dictate")
            st.markdown("""
            Click **New Session** above or run:
            ```bash
            python main.py
            ```
            """)
        
        with col2:
            st.markdown("### 📝 Modes")
            st.markdown("""
            - `clean` - Remove fillers
            - `rewrite` - Professional
            - `bullets` - Bullet points
            - `email` - Email format
            """)
        
        with col3:
            st.markdown("### 📁 Sessions")
            st.markdown("""
            Sessions auto-save with:
            - Timestamped filename
            - Auto-generated title
            - Organized summary
            """)
        
        # Recent sessions preview
        if sessions:
            st.markdown("---")
            st.subheader("📋 Recent Sessions")
            
            cols = st.columns(min(3, len(sessions)))
            for i, session in enumerate(sessions[:3]):
                with cols[i]:
                    content = read_session(session["path"])[:300]
                    st.markdown(f"**{session['name'][:30]}...**")
                    st.caption(content[:150] + "...")
                    if st.button("Open", key=f"open_{i}"):
                        st.session_state.selected_session = session["path"]
                        st.rerun()
    
    else:
        # Session View
        session_path = st.session_state.selected_session
        
        if not os.path.exists(session_path):
            st.error("Session file not found!")
            del st.session_state.selected_session
            st.rerun()
        
        content = read_session(session_path)
        
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.subheader(f"📄 {os.path.basename(session_path)}")
        with col2:
            edit_mode = st.toggle("✏️ Edit", value=st.session_state.get("edit_mode", False))
            st.session_state.edit_mode = edit_mode
        with col3:
            if st.button("❌ Close"):
                del st.session_state.selected_session
                st.rerun()
        
        st.divider()
        
        if edit_mode:
            # Edit mode
            edited_content = st.text_area(
                "Edit Document",
                value=content,
                height=500,
                label_visibility="collapsed"
            )
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("💾 Save", type="primary", use_container_width=True):
                    save_session(session_path, edited_content)
                    st.success("Saved!")
                    st.rerun()
            with col2:
                if st.button("🔄 Organize", use_container_width=True):
                    with st.spinner("Organizing..."):
                        editor = DocumentEditor()
                        organized = editor.edit(edited_content, mode="organize")
                        st.session_state.preview_content = organized
            with col3:
                if st.button("✨ Professional", use_container_width=True):
                    with st.spinner("Improving..."):
                        editor = DocumentEditor()
                        professional = editor.edit(edited_content, mode="professional")
                        st.session_state.preview_content = professional
            with col4:
                if st.button("📋 Actions", use_container_width=True):
                    with st.spinner("Extracting..."):
                        editor = DocumentEditor()
                        actions = editor.edit(edited_content, mode="action_items")
                        st.session_state.preview_content = actions
            
            # Preview
            if "preview_content" in st.session_state:
                st.markdown("---")
                st.subheader("Preview")
                st.markdown(st.session_state.preview_content)
                if st.button("Apply Preview"):
                    save_session(session_path, st.session_state.preview_content)
                    del st.session_state.preview_content
                    st.success("Applied!")
                    st.rerun()
        else:
            # View mode
            st.markdown(content)


if __name__ == "__main__":
    main()
