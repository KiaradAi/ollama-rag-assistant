from rag_engine import RAGEngine
from doc_loader import load_and_split_documents
import os, glob

engine = RAGEngine()

# پیدا کردن همه فایل‌ها در source_documents
files = glob.glob("source_documents/*")
print(f"Found {len(files)} files: {files}")

# بارگذاری و اضافه کردن
docs = load_and_split_documents(files)
print(f"Loaded {len(docs)} chunks")

if docs:
    engine.vector_store.add_documents(docs)
    print("Documents added to vector store.")
    print("Current files in DB:", engine.get_loaded_filenames())
