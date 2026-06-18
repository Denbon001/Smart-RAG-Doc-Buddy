import streamlit as st
import requests

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Your Doc Buddy",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

/* =====================================================
GLOBAL
===================================================== */

html, body, [class*="css"] {
    font-family: Arial;
}

/* =====================================================
MAIN CONTAINER
===================================================== */

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* =====================================================
TITLE
===================================================== */

.main-title {
    font-size: 64px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 8px;
}

/* =====================================================
SUBTITLE
===================================================== */

.sub-title {
    font-size: 22px;
    color: #9CA3AF;
    margin-bottom: 35px;
}

/* =====================================================
DOCUMENT SELECTOR
===================================================== */

.selector-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
    color: white;
}

/* =====================================================
QUERY BOX
===================================================== */

.query-box {
    background-color: #111827;
    padding: 18px;
    border-radius: 10px;
    border-left: 4px solid #2563EB;
    margin-top: 8px;
    margin-bottom: 20px;
}

/* =====================================================
RESPONSE BOX
===================================================== */

.response-box {
    background-color: #1F2937;
    padding: 22px;
    border-radius: 12px;
    margin-top: 10px;
    line-height: 1.7;
    font-size: 16px;
    color: #F3F4F6;
    border: 1px solid #374151;
}

/* =====================================================
HISTORY CARD
===================================================== */

.history-card {
    background-color: #161B22;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 14px;
    border: 1px solid #30363D;
}

/* =====================================================
LABELS
===================================================== */

.label-text {
    font-size: 17px;
    font-weight: bold;
    color: white;
    margin-bottom: 4px;
}

/* =====================================================
CHAT TEXT
===================================================== */

.chat-text {
    font-size: 15px;
    line-height: 1.6;
    color: #E5E7EB;
}

/* =====================================================
CONTEXT
===================================================== */

.context-text {
    color: #9CA3AF;
    font-size: 14px;
    margin-top: 10px;
    font-style: italic;
}

/* =====================================================
DIVIDER
===================================================== */

.custom-divider {
    margin-top: 28px;
    margin-bottom: 28px;
    border-top: 1px solid #30363D;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
<div class="main-title">
Your Doc Buddy!!
</div>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
<div class="sub-title">
Smart RAG Research Assistant for Documents
</div>
""",
    unsafe_allow_html=True
)

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("📄 Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose Files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    # =================================================
    # PROCESS BUTTON
    # =================================================

    if uploaded_files:

        if st.button("Process Documents"):

            with st.spinner("Indexing Documents..."):

                success_count = 0

                for uploaded_file in uploaded_files:

                    try:

                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file,
                                uploaded_file.type
                            )
                        }

                        response = requests.post(
                            "http://127.0.0.1:8000/upload",
                            files=files,
                            timeout=120
                        )

                        if response.status_code == 200:

                            success_count += 1

                    except Exception as e:

                        st.error(f"Upload Failed: {e}")

                st.success(
                    f"{success_count} Documents Indexed Successfully"
                )

# =====================================================
# GET DOCUMENTS
# =====================================================

documents = []

try:

    response = requests.get(
        "http://127.0.0.1:8000/documents"
    )

    if response.status_code == 200:

        documents = response.json().get(
            "documents",
            []
        )

except Exception:

    documents = []

# =====================================================
# DOCUMENT SELECTOR
# =====================================================

st.markdown(
    """
<div class="selector-title">
Select Document
</div>
""",
    unsafe_allow_html=True
)

selected_document = st.selectbox(
    "Select Document",
    documents if documents else ["No Documents Uploaded"],
    label_visibility="collapsed"
)

# =====================================================
# QUESTION INPUT
# =====================================================

query = st.text_input(
    "Ask questions related to uploaded documents only."
)

# =====================================================
# ASK QUESTION
# =====================================================

if query:

    # =================================================
    # NO DOCUMENT
    # =================================================

    if selected_document == "No Documents Uploaded":

        st.error(
            "Please upload documents first."
        )

    else:

        with st.spinner(
            "Give me a second, just flipping through the pages..."
        ):

            try:

                response = requests.get(
                    "http://127.0.0.1:8000/ask",
                    params={
                        "query": query,
                        "selected_document": selected_document
                    },
                    timeout=120
                )

                if response.status_code == 200:

                    data = response.json()

                    answer = data["answer"]

                    # =====================================
                    # SAVE CHAT
                    # =====================================

                    st.session_state.chat_history.append({

                        "document": selected_document,
                        "question": query,
                        "answer": answer

                    })

                    # =====================================
                    # PREVIOUS CONVERSATIONS
                    # =====================================

                    history = [

                        chat

                        for chat in st.session_state.chat_history[:-1]

                        if chat["document"] == selected_document
                    ]

                    if history:

                        st.markdown(
                            "## Previous Conversations"
                        )

                        for chat in reversed(history):

                            short_answer = (

                                chat["answer"][:220] + "..."

                                if len(chat["answer"]) > 220

                                else chat["answer"]
                            )

                            st.markdown(f"""
<div class="history-card">

<div class="label-text">
USER:
</div>

<div class="chat-text">
{chat['question']}
</div>

<br>

<div class="label-text">
AI:
</div>

<div class="chat-text">
{short_answer}
</div>

<div class="context-text">
Context from selected document
</div>

</div>
""", unsafe_allow_html=True)

                    # =====================================
                    # DIVIDER
                    # =====================================

                    st.markdown(
                        '<div class="custom-divider"></div>',
                        unsafe_allow_html=True
                    )

                    # =====================================
                    # QUERY
                    # =====================================

                    st.markdown("## Query")

                    st.markdown(f"""
<div class="query-box">
{query}
</div>
""", unsafe_allow_html=True)

                    # =====================================
                    # RESPONSE
                    # =====================================

                    st.markdown("## Response")

                    st.markdown(f"""
<div class="response-box">
{answer}
</div>
""", unsafe_allow_html=True)

                else:

                    st.error("Backend Error")

            except Exception as e:

                st.error(f"Error: {e}")