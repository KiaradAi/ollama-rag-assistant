import os
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, BSHTMLLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

def load_and_split_documents(file_paths: list[str], chunk_size: int = 1000, chunk_overlap: int = 150) -> list[Document]:
    """Loads documents from various file types, extracts text, and splits them into chunks."""
    docs = []
    print(f"Using chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Load documents from file paths
    for file_path in file_paths:
        file_extension = os.path.splitext(file_path)[1].lower()
        loaded_docs = []
        try:
            if file_extension == ".pdf":
                loader = PyMuPDFLoader(file_path)
                loaded_docs = loader.load()
            elif file_extension in [".doc", ".docx"]:
                loader = Docx2txtLoader(file_path)
                loaded_docs = loader.load()
            elif file_extension == ".html":
                loader = BSHTMLLoader(file_path, open_encoding='utf-8')
                loaded_docs = loader.load()
            elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                text = ocr_image(file_path)
                if text:
                    metadata = {"source": os.path.basename(file_path)}
                    loaded_docs = [Document(page_content=text, metadata=metadata)]
            elif file_extension == ".txt":
                 with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                 metadata = {"source": os.path.basename(file_path)}
                 loaded_docs = [Document(page_content=text, metadata=metadata)]

            # Handle metadata for each document
            if loaded_docs:
                for doc in loaded_docs:
                    if 'source' not in doc.metadata or not doc.metadata['source']:
                        doc.metadata['source'] = os.path.basename(file_path)
                    elif not doc.metadata['source'] == os.path.basename(file_path):
                        doc.metadata['source'] = os.path.basename(file_path)

                split_docs = text_splitter.split_documents(loaded_docs)
                docs.extend(split_docs)
            else:
                print(f"Warning: Could not load or process file: {file_path}. Unsupported format or empty content.")

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    return docs

def ocr_image(image_path: str) -> str:
    """Performs OCR on an image file and returns the extracted text."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        print("Tesseract is not installed or not in PATH. OCR functionality will not work.")
        print("Please install Tesseract: https://github.com/tesseract-ocr/tesseract#installing-tesseract")
        return ""
    except Exception as e:
        print(f"Error during OCR for image {image_path}: {e}")
        return ""