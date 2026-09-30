<div align="center">

<img src="media/application-snippet.png" alt="Local RAG Assistant" width="200">

# 🧠 Local RAG Assistant

**Your documents. Your machine. Your answers.**

A fully local, privacy-first Retrieval-Augmented Generation (RAG) assistant that lets you chat with your PDFs, Word documents, text files, and even images — **without sending a single byte to the cloud**.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.30-1C3C3C?style=for-the-badge)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.23-FF6B6B?style=for-the-badge)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge)](https://ollama.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Quick Start](#-quick-start) • [Tech Stack](#-tech-stack) • [Contributing](#-contributing)

</div>

---

## 📖 About

**Local RAG Assistant** is a self-contained AI assistant that runs entirely on your local machine. It combines the power of large language models (via **Ollama**) with a vector database (**ChromaDB**) to retrieve relevant information from your own documents and generate accurate, context-aware answers.

**No API keys. No subscriptions. No data leaves your computer.**

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| 🔒 **100% Local & Private** | All processing happens on your machine. No internet required after setup. |
| 📄 **Multi-Format Support** | Ingest PDF, DOCX, TXT, PNG, JPG, TIFF, and HTML files. |
| 🔍 **Semantic Search** | Finds relevant information by meaning, not just keywords. |
| 🧠 **Conversational Memory** | Remembers your chat history for natural conversations. |
| 🖼️ **OCR Support** | Extracts text from images using Tesseract OCR. |
| 🎨 **Clean Web UI** | Built with Streamlit for a smooth, interactive experience. |
| ⚡ **Lightweight Models** | Works with models as small as 0.5B parameters. |
| 🐳 **Docker Support** | Easy deployment with Docker and GitHub Packages. |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9** — [Download](https://www.python.org/downloads/release/python-3913/)
- **Ollama** — [Download](https://ollama.com/download)
- **Tesseract OCR** — Install via: `winget install UB-Mannheim.TesseractOCR`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/KiaradAi/ollama-rag-assistant.git
cd ollama-rag-assistant

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 5. Add your documents to source_documents/

# 6. Index your documents
python index_docs.py

# 7. Launch the assistant
python -m streamlit run app.py
