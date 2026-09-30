from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from doc_loader import load_and_split_documents

# Configuration
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "Model.llama.3.1-8b:latest"

class RAGEngine:
    def __init__(self, persist_directory: str = CHROMA_DB_PATH, k_memory: int = 3, initial_chat_history: list = None):
        """Initializes the RAG engine with conversational memory, optionally loading past history."""
        self.persist_directory = persist_directory
        self.embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        
        print(f"Initializing vector store from/at {self.persist_directory}")
        self.vector_store = Chroma(persist_directory=self.persist_directory, 
                                 embedding_function=self.embedding_function)
        
        self.llm = OllamaLLM(model=OLLAMA_MODEL)
        self.retriever = self.vector_store.as_retriever()

        # Initialize memory FIRST
        self.memory = ConversationBufferWindowMemory(
            k=k_memory, 
            memory_key="chat_history", 
            return_messages=True, 
            output_key='answer'
        )

        # Load initial history into memory if provided
        if initial_chat_history:
            print(f"Loading {len(initial_chat_history)} messages from persisted history into memory...")
            # Ensure history is structured as pairs of user/assistant messages
            for i in range(0, len(initial_chat_history) - 1, 2):
                user_msg = initial_chat_history[i]
                assistant_msg = initial_chat_history[i+1]
                # Check roles before saving context
                if user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant":
                    self.memory.save_context(
                        {"question": user_msg["content"]}, 
                        {"answer": assistant_msg["content"]}
                    )
                else:
                    print(f"Warning: Skipping unexpected message pair order at index {i} in initial history.")
            # Handle potential trailing user message (optional, usually not needed for context)
            if len(initial_chat_history) % 2 != 0:
                print(f"Warning: Trailing user message found in initial history at index {len(initial_chat_history)-1}, not loaded into memory context.")

        # Setup the ConversationalRetrievalChain AFTER memory is potentially populated
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory, # Pass the potentially primed memory
            return_source_documents=True,
            output_key='answer'
        )

    def get_loaded_filenames(self) -> list[str]:
        """Retrieves a list of unique source filenames from the vector store."""
        try:
            # Retrieve metadata for all documents. 
            # Chroma's get() is the standard way.
            # Use a reasonable limit or handle potential large results if necessary.
            metadata = self.vector_store.get(include=["metadatas"]) 
            
            # Extract and normalize the 'source' field from each metadata dictionary
            sources = [
                meta.get('source', '').strip().lower() 
                for meta in metadata.get('metadatas', []) if meta and meta.get('source')
            ]
            
            # Return a sorted list of unique filenames
            return sorted(list(set(sources)))
        except Exception as e:
            print(f"Error retrieving filenames from vector store: {e}")
            return []

    def add_documents(self, file_paths: list[str]):
        """Loads, splits, and adds documents to the vector store."""
        print(f"Loading and splitting documents: {file_paths}")
        documents = load_and_split_documents(file_paths)
        if documents:
            print(f"Adding {len(documents)} document chunks to the vector store...")
            self.vector_store.add_documents(documents)
            print("Documents added to vector store.")
        else:
            print("No valid document chunks to add.")

    def query(self, question: str) -> dict:
        """Queries the conversational RAG chain."""
        print(f"Querying conversational RAG chain with: '{question}'")
        # The chain now manages history via the memory object.
        # We only need to pass the new question.
        # The input structure might depend slightly on the chain version, 
        # but passing a dict with 'question' is standard.
        result = self.qa_chain.invoke({"question": question})
        print("Query completed.")
        # Result dictionary should contain 'question', 'chat_history' (from memory), 
        # 'answer' (the LLM response), and 'source_documents'.
        return result
