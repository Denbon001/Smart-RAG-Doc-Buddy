import os
import re

from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document  # <-- PAGE TRACKING FOR ALL TYPES

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance
)

# =====================================================
# LOAD ENV
# =====================================================

load_dotenv()

# =====================================================
# EMBEDDING MODEL
# =====================================================

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# =====================================================
# OLLAMA MODEL
# =====================================================

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "tinyllama"
)

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0.0,
    num_predict=80,
    top_k=5,
    top_p=0.1
)

# =====================================================
# QDRANT LOCAL STORAGE
# =====================================================

os.makedirs(
    "qdrant_storage",
    exist_ok=True
)

client = QdrantClient(
    path="./qdrant_storage"
)

# =====================================================
# CLEAN TEXT
# =====================================================

def clean_text(text):

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =====================================================
# EMPTY RESPONSE
# =====================================================

def empty_response():

    return """
Definition:
Insufficient information found.

Explanation:
The answer could not be found in the selected document.

Key Points:
- Ask questions related to uploaded files
- Select the correct document
- Upload academic documents only
"""

# =====================================================
# COLLECTION NAME
# =====================================================

def create_collection_name(filename):

    name = os.path.splitext(filename)[0]

    name = re.sub(
        r"[^a-zA-Z0-9]",
        "_",
        name
    )

    return f"doc_{name.lower()}"

# =====================================================
# CREATE COLLECTION
# =====================================================

def ensure_collection_exists(collection_name):

    try:

        client.get_collection(collection_name)

    except Exception:

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

# =====================================================
# VECTOR STORE
# =====================================================

def get_vectorstore(collection_name):

    ensure_collection_exists(collection_name)

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )

# =====================================================
# DOCUMENT LIST
# =====================================================

def get_uploaded_documents():

    try:

        collections = client.get_collections().collections

        documents = []

        for collection in collections:

            name = collection.name

            if name.startswith("doc_"):

                clean_name = name.replace(
                    "doc_",
                    ""
                )

                clean_name = clean_name.replace(
                    "_",
                    " "
                )

                documents.append(clean_name)

        return sorted(documents)

    except Exception:

        return []

# =====================================================
# PROCESS DOCUMENT
# =====================================================

def process_document(file_path):

    print("PROCESSING DOCUMENT")

    filename = os.path.basename(file_path)

    collection_name = create_collection_name(
        filename
    )

    # =================================================
    # FILE TYPE (WITH STRUCTURAL PAGE TRACKING)
    # =================================================

    if file_path.endswith(".pdf"):

        loader = PyPDFLoader(file_path)
        docs = loader.load()

    elif file_path.endswith(".docx"):

        loader = Docx2txtLoader(file_path)
        raw_docs = loader.load()
        docs = []
        for doc in raw_docs:
            text_blocks = [doc.page_content[i:i+2000] for i in range(0, len(doc.page_content), 2000)]
            for idx, block in enumerate(text_blocks):
                docs.append(Document(page_content=block, metadata={"source": file_path, "page": idx}))

    elif file_path.endswith(".txt"):

        loader = TextLoader(file_path, encoding="utf-8")
        raw_docs = loader.load()
        docs = []
        for doc in raw_docs:
            text_blocks = [doc.page_content[i:i+2000] for i in range(0, len(doc.page_content), 2000)]
            for idx, block in enumerate(text_blocks):
                docs.append(Document(page_content=block, metadata={"source": file_path, "page": idx}))

    else:

        return "Unsupported File Type"

    # =================================================
    # SPLITTER
    # =================================================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " "
        ]
    )

    splits = splitter.split_documents(docs)

    # =================================================
    # DELETE OLD COLLECTION
    # =================================================

    try:

        client.delete_collection(
            collection_name
        )

    except Exception:

        pass

    ensure_collection_exists(
        collection_name
    )

    # =================================================
    # VECTOR STORE
    # =================================================

    vectorstore = get_vectorstore(
        collection_name
    )

    vectorstore.add_documents(
        splits
    )

    print("DOCUMENT INDEXED SUCCESSFULLY")

    return "Document Indexed Successfully"

# =====================================================
# QUERY VALIDATION
# =====================================================

def is_query_related(query, context):

    query = query.lower()

    context = context.lower()

    query_words = re.findall(
        r"\w+",
        query
    )

    query_words = [

        word

        for word in query_words

        if len(word) > 2
    ]

    matches = 0

    for word in query_words:

        if word in context:

            matches += 1

    return matches >= 1

# =====================================================
# CLEAN GENERATED ANSWER
# =====================================================

def clean_generated_answer(answer):

    answer = clean_text(answer)

    blocked_phrases = [

        "very important rules",
        "good example",
        "bad example",
        "response format",
        "instruction",
        "as an ai",
        "language model",
        "chatgpt",
        "openai"
    ]

    answer_lower = answer.lower()

    for phrase in blocked_phrases:

        if phrase in answer_lower:

            return None

    return answer.strip()

# =====================================================
# GET ANSWER
# =====================================================

def get_answer(
    query,
    selected_document
):

    print(f"QUESTION: {query}")

    query_lower = query.lower()

    # =================================================
    # BLOCK UNRELATED QUESTIONS
    # =================================================

    blocked_queries = [

        "joke",
        "funny",
        "story",
        "movie",
        "song",
        "who are you",
        "chatgpt",
        "openai",
        "your name",
        "girlfriend",
        "boyfriend",
        "weather",
        "news",
        "politics",
        "cricket",
        "football"
    ]

    for word in blocked_queries:

        if word in query_lower:

            return """
Definition:
Unrelated question detected.

Explanation:
This assistant answers questions only from uploaded documents.

Key Points:
- Ask syllabus or document-related questions
- External/general questions are not supported
- Select the correct uploaded document
"""

    # =================================================
    # COLLECTION NAME
    # =================================================

    collection_name = create_collection_name(
        selected_document
    )

    # =================================================
    # CHECK COLLECTION
    # =================================================

    try:

        client.get_collection(collection_name)

    except Exception:

        return """
Definition:
No document found.

Explanation:
The selected document has not been uploaded yet.

Key Points:
- Upload the document first
- Select the correct document
"""

    # =================================================
    # VECTOR STORE
    # =================================================

    vectorstore = get_vectorstore(
        collection_name
    )

    # =================================================
    # RETRIEVER
    # =================================================

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 12
        }
    )

    docs = retriever.invoke(query)

    # =================================================
    # NO DOCUMENTS
    # =================================================

    if not docs:

        return empty_response()

    # =================================================
    # CONTEXT & SOURCE EXTRACTION
    # =================================================

    context = ""

    sources = []

    for doc in docs:

        content = clean_text(
            doc.page_content
        )

        context += content + "\n\n"

        source = os.path.basename(
            doc.metadata.get(
                "source",
                "Unknown"
            )
        )

        page = doc.metadata.get(
            "page",
            "N/A"
        )
        
        # Shift 0-indexed pages up by 1
        if isinstance(page, int):
            page += 1

        sources.append(
            f"{source} | Page {page}"
        )

    # =================================================
    # LIMIT CONTEXT & COMPILE EARLY SOURCES
    # =================================================

    context = context[:2500]
    
    unique_sources = list(set(sources))
    source_text = ", ".join(unique_sources)

    # =================================================
    # QUERY VALIDATION
    # =================================================

    if not is_query_related(query, context):

        return empty_response()

    # =================================================
    # HOW MANY UNITS HANDLER
    # =================================================

    if (
        "how many unit" in query_lower
        or "how many units" in query_lower
        or "total unit" in query_lower
        or "total units" in query_lower
    ):

        try:

            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=200,
                with_payload=True,
                with_vectors=False
            )

            points = scroll_result[0]

            full_text = ""

            for point in points:

                payload = point.payload

                if "page_content" in payload:

                    full_text += payload["page_content"] + "\n"

            units = re.findall(
                r"Unit\s*\d+",
                full_text,
                re.IGNORECASE
            )

            unique_units = sorted(set(units))

            if not unique_units:

                return empty_response()

            return f"""
Definition:
Total Units: {len(unique_units)}

Explanation:
Units found in uploaded document:

{", ".join(unique_units)}

Key Points:
- Extracted directly from full document
- No external knowledge used

<br>

<p style="font-style: italic; color: gray;">

Context:
from {selected_document} (Full Document Scan)

</p>
"""

        except Exception:

            return empty_response()

    # =================================================
    # UNIT EXTRACTION HANDLER
    # =================================================

    unit_match = re.search(
        r"unit\s*(\d+)",
        query_lower
    )

    if unit_match:

        unit_number = unit_match.group(1)

        pattern = rf"(Unit\s*{unit_number}.*?)(Unit\s*\d+|$)"

        match = re.search(
            pattern,
            context,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            extracted_text = match.group(1)

            extracted_text = clean_text(
                extracted_text
            )

            return f"""
Definition:
Unit {unit_number} Contents

Explanation:
{extracted_text}

Key Points:
- Extracted directly from uploaded document
- No external knowledge used

<br>

<p style="font-style: italic; color: gray;">

Context:
from {source_text}

</p>
"""

    # =================================================
    # WHAT IS HANDLER
    # =================================================

    if (
        "what is" in query_lower
        or "wha is" in query_lower
        or "define" in query_lower
    ):

        topic = query_lower
        for keyword in ["what is", "wha is", "define"]:
            topic = topic.replace(keyword, "")
        topic = topic.strip()

        matching_sentences = []

        sentences = re.split(
            r"[.\n]",
            context
        )

        for sentence in sentences:

            if topic.lower() in sentence.lower():

                matching_sentences.append(
                    clean_text(sentence)
                )

        if matching_sentences:

            extracted = " ".join(
                matching_sentences[:3]
            )

            return f"""
Definition:
{extracted}

Explanation:
Topic found in uploaded document.

Key Points:
- Extracted directly from syllabus
- No external knowledge used

<br>

<p style="font-style: italic; color: gray;">

Context:
from {source_text}

</p>
"""

        return f"""
Definition:
{topic.title()} is included in the uploaded syllabus.

Explanation:
The syllabus contains topics related to {topic}.

Key Points:
- Topic detected from uploaded document
- No external textbook explanation used

<br>

<p style="font-style: italic; color: gray;">

Context:
from {source_text}

</p>
"""

    # =================================================
    # DEFAULT PROMPT
    # =================================================

    prompt = f"""
Context:
{context}

Question:
{query}

Answer briefly using only the context.

Do not use outside knowledge.

Answer:
"""

    # =================================================
    # GENERATE (WITH PROMPT LEAKAGE FIX)
    # =================================================

    try:

        response = llm.invoke(prompt)

        answer = response.content.strip()
        
        # Clean up model structural leakage
        if "answer:" in answer.lower():
            answer = re.split(r"answer:\s*", answer, flags=re.IGNORECASE)[-1].strip()
        elif "question:" in answer.lower():
            answer = re.sub(r"question:.*?\n", "", answer, flags=re.IGNORECASE).strip()

    except Exception:

        return empty_response()

    # =================================================
    # CLEAN RESPONSE
    # =================================================

    answer = clean_generated_answer(
        answer
    )

    if not answer:

        return empty_response()

    # =================================================
    # FINAL RESPONSE (FALLBACK LLM ROUTE)
    # =================================================

    final_answer = f"""
Definition:
{answer}

Explanation:
Information retrieved directly from the uploaded document.

Key Points:
- Based on document context
- Retrieved using RAG pipeline
- No external knowledge used

<br>

<p style="font-style: italic; color: gray;">

Context:
from {source_text}

</p>
"""

    return final_answer