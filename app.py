import streamlit as st
import os
import json
from datetime import datetime
from rag_engine import RAGEngine, OLLAMA_MODEL

# --- Set Page Config ---
st.set_page_config(
    page_title="Local RAG Assistant", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration Constants---
SOURCE_DOCS_DIR = "source_documents"
CHAT_HISTORY_FILE = "chat_history.json"
ALLOWED_EXTENSIONS = { 
    ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt",
    ".html" 
}
CHROMA_DB_PATH = "./chroma_db" # Define path for deletion

def load_chat_history():
    """Loads chat history from the JSON file."""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r') as f:
                history = json.load(f)
                if isinstance(history, list):
                    return history
                else:
                    print(f"Chat history file '{CHAT_HISTORY_FILE}' has invalid format (not a list). Starting fresh.")
                    return []
        except json.JSONDecodeError:
            st.error(f"Error reading chat history file '{CHAT_HISTORY_FILE}'. Starting fresh.")
            print(f"JSONDecodeError in chat history file '{CHAT_HISTORY_FILE}'. Starting fresh.")
            return []
        except Exception as e:
            st.error(f"An unexpected error occurred loading chat history: {e}")
            print(f"Unexpected error loading chat history: {e}")
            return []
    return []


def save_chat_history(history):
    """Saves chat history to the JSON file."""
    try:
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        st.error(f"Failed to save chat history: {e}")
        print(f"Failed to save chat history to {CHAT_HISTORY_FILE}: {e}")


# --- Initialization ---
# Load chat history first
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = load_chat_history()
    print(f"Chat history loaded ({len(st.session_state.chat_history)} messages).")
    initial_history_for_engine = st.session_state.chat_history
else:
    initial_history_for_engine = None # Don't pass history if already in session

# Initialize RAG engine (might load existing DB)
if 'rag_engine' not in st.session_state:
    try:
        st.session_state.rag_engine = RAGEngine(initial_chat_history=initial_history_for_engine)
        print("RAG Engine initialized successfully.")
        # RESTORE docs_loaded_on_startup flag initialization
        st.session_state.docs_loaded_on_startup = False 
    except Exception as e:
        st.error(f"Failed to initialize RAG Engine: {e}")
        print(f"Critical Error: Failed to initialize RAG Engine: {e}")
        st.session_state.rag_engine = None
        # Set flag to true if engine fails to prevent load attempts
        st.session_state.docs_loaded_on_startup = True 

# Initialize loaded filenames list
if 'loaded_filenames' not in st.session_state:
    st.session_state.loaded_filenames = []

# --- Populate Filename List from DB (if not first startup) ---
if st.session_state.rag_engine and st.session_state.get('docs_loaded_on_startup', False):
     # If the list is empty, try fetching from DB
     if not st.session_state.loaded_filenames:
        print("Attempting to fetch known documents from persisted database...")
        try:
            st.session_state.loaded_filenames = st.session_state.rag_engine.get_loaded_filenames()
            if st.session_state.loaded_filenames:
                print(f"Found {len(st.session_state.loaded_filenames)} documents in existing DB.")
            else:
                print("Persisted DB is empty or contains no documents with source metadata.")
        except Exception as e:
            print(f"Error fetching documents from DB: {e}")
            st.session_state.loaded_filenames = []

# --- Auto-load Documents on FIRST Startup ONLY ---
if st.session_state.rag_engine and not st.session_state.get('docs_loaded_on_startup', True):
    print("Attempting automatic document load on first startup...")
    st.session_state.docs_loaded_on_startup = True # Mark that we've attempted the load
    
    with st.spinner("Scanning source directory and loading documents... (This may take a while)"):
        startup_message = None
        if not os.path.isdir(SOURCE_DOCS_DIR):
            startup_message = ("warning", f"Source directory '{SOURCE_DOCS_DIR}' not found.")
            print(f"Warning: Source directory '{SOURCE_DOCS_DIR}' not found during startup.")
            files_to_process = []
        else:
            files_to_process = []
            try:
                all_files = [os.path.join(SOURCE_DOCS_DIR, f) for f in os.listdir(SOURCE_DOCS_DIR) if os.path.isfile(os.path.join(SOURCE_DOCS_DIR, f))]
                files_to_process = [f for f in all_files if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS]
                print(f"Startup Scan: Found {len(files_to_process)} files with allowed extensions in '{SOURCE_DOCS_DIR}'.")
            except Exception as e:
                startup_message = ("error", f"Startup Scan: Error scanning directory '{SOURCE_DOCS_DIR}': {e}")
                print(f"Startup Scan: Error scanning directory '{SOURCE_DOCS_DIR}': {e}")
                files_to_process = []

            if not files_to_process:
                if not startup_message: # Don't overwrite scan error
                    startup_message = ("info", f"No documents found in '{SOURCE_DOCS_DIR}' during startup.")
                st.session_state.loaded_filenames = []
            else:
                # Files found, attempt processing
                try:
                    st.session_state.rag_engine.add_documents(files_to_process)
                    st.session_state.loaded_filenames = sorted([os.path.basename(f) for f in files_to_process])
                    startup_message = ("success", f"Successfully loaded {len(files_to_process)} file(s) from '{SOURCE_DOCS_DIR}'.")
                    print("Startup document load successful.")
                except Exception as e:
                    error_msg = f"Startup Load Error: Failed processing documents from '{SOURCE_DOCS_DIR}': {e}"
                    startup_message = ("error", error_msg)
                    st.session_state.loaded_filenames = []
                    print(error_msg)
    
    if startup_message:
        st.session_state.startup_message_display = startup_message 

# --- Streamlit UI ---
st.title("Local RAG Assistant")
st.caption(f"Chat with your documents, running entirely locally with Retrieval-Augmented Generation and {OLLAMA_MODEL}.")

# Display startup messages (if any) - outside the spinner block
if 'startup_message_display' in st.session_state and st.session_state.startup_message_display:
    msg_type, msg_content = st.session_state.startup_message_display
    if msg_type == "success":
        st.success(msg_content, icon="✅")
    elif msg_type == "info":
        st.info(msg_content, icon="ℹ️")
    elif msg_type == "warning":
        st.warning(msg_content, icon="⚠️")
    elif msg_type == "error":
        st.error(msg_content)
    # Clear the message after displaying it once
    del st.session_state.startup_message_display

# --- Document Management Section (Sidebar) ---
with st.sidebar:
    # Inject custom CSS for the white header and filenames
    st.markdown("""
    <style>
    .sidebar-header-white {
        color: white !important; 
    }
    .filename-white {
        color: white !important; 
        font-family: monospace; 
        background-color: #555555 !important; /* Add a dark gray background */
        font-size: 0.85em !important; /* Make font slightly smaller */
        padding: 2px 5px !important; /* Add small vertical and horizontal padding */
        border-radius: 3px !important; /* Slightly rounded corners */
        display: inline-block; /* Ensure background covers only the text */
        margin-bottom: 3px; /* Add a little space below each filename */
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display Loaded Documents List (Reflects persisted DB state)
    st.subheader("Known Documents in DB") 
    st.markdown(f"Source Folder: <span class='filename-white'>{SOURCE_DOCS_DIR}</span>", unsafe_allow_html=True)
    if 'loaded_filenames' in st.session_state and st.session_state.loaded_filenames:
        for filename in st.session_state.loaded_filenames:
            st.markdown(f"<span class='filename-white'>{filename}</span>", unsafe_allow_html=True)
    else:
        st.info("No documents found in database.")

    # --- Manage Assistant Section --- 
    st.markdown("--- ")
    st.header("Manage Assistant") 
    
    # Clear Chat History button (Stays in this section)
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        print("Chat history cleared from session state.")
        try:
            if os.path.exists(CHAT_HISTORY_FILE):
                os.remove(CHAT_HISTORY_FILE)
                st.toast("Chat history file deleted.", icon="✅")
                print(f"Deleted chat history file: {CHAT_HISTORY_FILE}")
            else:
                st.toast("Chat history file already deleted or doesn't exist.", icon="ℹ️")
        except Exception as e:
            st.toast(f"Error deleting chat history file: {e}", icon="❌")
            print(f"Error deleting chat history file {CHAT_HISTORY_FILE}: {e}")

# --- Chat History Display ---
st.header("Chat")

# Display existing messages from history
if 'chat_history' in st.session_state and st.session_state.chat_history:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display sources (as unique filenames) if they exist for assistant messages
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                # Sources are stored as list of dicts: {'page_content': ..., 'metadata': {'source': ...}}
                source_list = message["sources"]
                if isinstance(source_list, list) and source_list:
                    # Extract filenames from metadata, normalizing them
                    filenames = [
                        s.get("metadata", {}).get("source", "").strip().lower() # Normalize here
                        for s in source_list 
                        if s.get("metadata", {}).get("source")
                    ]
                    # Get unique, sorted filenames (Set handles uniqueness after normalization)
                    unique_filenames = sorted(list(set(filenames)))
                    
                    if unique_filenames:
                         with st.expander("View Sources"):
                            # Display only the unique filenames
                            for filename in unique_filenames:
                                # Use the same styling as the sidebar list
                                st.markdown(f"<span class='filename-white'>{filename}</span>", unsafe_allow_html=True)

else:
    st.info("Start chatting by typing your question below!")

# --- Chat Input Area ---
if prompt := st.chat_input("Ask a question about your documents..."):
    if not st.session_state.rag_engine:
        st.error("Cannot process query: RAG Engine is not initialized.")
    else:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Query RAG engine and display response
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.rag_engine.query(prompt)
                
                # Extract answer (using the specified output_key)
                answer = response.get('answer', "Sorry, I couldn't find an answer based on the conversation history and documents.")
                source_documents = response.get('source_documents', [])

                # Convert source Document objects to serializable format for JSON
                serializable_sources = [
                    {"page_content": doc.page_content, "metadata": doc.metadata}
                    for doc in source_documents
                ]

                # Add assistant response to chat history (including sources)
                assistant_message = {
                    "role": "assistant",
                    "content": answer,
                    "sources": serializable_sources, 
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.chat_history.append(assistant_message)

                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    # Display sources using the correct logic (unique filenames)
                    if source_documents: 
                        # Extract filenames from the returned Document objects, normalizing them
                        filenames = [
                            doc.metadata.get('source', '').strip().lower() 
                            for doc in source_documents 
                            if doc.metadata.get('source')
                        ]
                        # Get unique, sorted filenames
                        unique_filenames = sorted(list(set(filenames)))

                        if unique_filenames:
                            with st.expander("View Sources"):
                                # Display only the unique filenames with styling
                                for filename in unique_filenames:
                                    st.markdown(f"<span class='filename-white'>{filename}</span>", unsafe_allow_html=True)

                # Save updated chat history to JSON file
                save_chat_history(st.session_state.chat_history)

            except Exception as e:
                error_message = f"Error querying RAG engine: {e}"
                st.error(error_message)
                print(error_message)
                # Add error message to chat display (optional)
                with st.chat_message("assistant"):
                     st.error(f"An error occurred: {e}")
                 # Save history even if there was an error during query
                save_chat_history(st.session_state.chat_history) 