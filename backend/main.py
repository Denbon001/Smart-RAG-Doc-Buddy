import os
import shutil

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form
)

from backend.engine import (
    process_document,
    get_answer,
    get_uploaded_documents
)

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(
    title="Your Doc Buddy",
    version="4.0"
)

# =====================================================
# ROOT
# =====================================================

@app.get("/")
async def root():

    return {
        "message": "Your Doc Buddy Backend Running"
    }

# =====================================================
# UPLOAD DOCUMENT
# =====================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    try:

        # =================================================
        # CREATE DATA FOLDER
        # =================================================

        os.makedirs(
            "data",
            exist_ok=True
        )

        # =================================================
        # SAVE FILE
        # =================================================

        file_path = os.path.join(
            "data",
            file.filename
        )

        with open(file_path, "wb") as f:

            shutil.copyfileobj(
                file.file,
                f
            )

        # =================================================
        # PROCESS DOCUMENT
        # =================================================

        status = process_document(file_path)

        return {
            "status": status,
            "filename": file.filename
        }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }

# =====================================================
# GET DOCUMENT LIST
# =====================================================

@app.get("/documents")
async def documents():

    try:

        docs = get_uploaded_documents()

        return {
            "documents": docs
        }

    except Exception as e:

        return {
            "documents": [],
            "error": str(e)
        }

# =====================================================
# ASK QUESTION
# =====================================================

@app.get("/ask")
async def ask_question(

    query: str,
    selected_document: str

):

    try:

        response = get_answer(
            query=query,
            selected_document=selected_document
        )

        return {
            "answer": response
        }

    except Exception as e:

        return {
            "answer": f"Backend Error: {str(e)}"
        }