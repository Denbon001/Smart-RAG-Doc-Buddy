# Smart RAG for Documents (Your Doc Buddy!!) 🤖📄

An advanced, local Retrieval-Augmented Generation (RAG) system built to process uploaded documents, perform precise semantic search, and deliver context-aware answers using a local LLM workflow.

---

## 🚀 Features
- **Semantic Information Retrieval:** Uses HuggingFace embeddings and Qdrant Vector DB to accurately fetch exact source contexts.
- **Source Tracking:** Every generated response tracks and highlights the exact source page from your uploaded documents.
- **Clean Architecture:** Fully decoupled architecture featuring a fast backend API service and a responsive UI.

---

## 🛠️ Tech Stack
- **Backend Framework:** FastAPI (Python)
- **Vector Database:** Qdrant DB
- **Embeddings:** HuggingFace Embeddings
- **LLM Workflow:** Local LLM Pipeline
- **Frontend / UI:** Python (Streamlit / App framework)
- **Language Model:** Tinyllama (Ollama)

---

## 📁 Repository Structure
```text
RESEARCH_RAG/
│
├── backend/          # FastAPI server, embedding logic, and Qdrant retrieval engine
│   ├── engine.py
│   └── main.py
│
├── frontend/         # User interface and client-side interactions
│   └── app.py
│
└── requirements.txt  # Project library dependencies
