"""
HomeAI - LangChain + Streamlit Chatbot
=====================================
How to run:
    streamlit run web_chatbot.py

Browser will automatically open at http://localhost:8501
"""

import os
import sys
import base64
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from PIL import Image
from prompts import PromptTemplates

# Load environment variables from .env file
load_dotenv()

# Get environment variables
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "local-model")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LANGUAGE = os.getenv("LANGUAGE", "ja")  # Default to Japanese


def get_base_path() -> Path:
    """Return base path for both source and PyInstaller bundle execution."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_static_image_path(filename: str) -> Path:
    """Return a static image path."""
    return get_base_path() / "static" / filename


def load_image(filename: str) -> Image.Image | None:
    """Load a static image if it exists."""
    image_path = get_static_image_path(filename)
    if image_path.exists():
        return Image.open(image_path)
    return None


def get_image_data_uri(filename: str) -> str | None:
    """Return a static image as a data URI."""
    image_path = get_static_image_path(filename)
    if not image_path.exists():
        return None

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


PAGE_ICON = load_image("homeai_logo@2x.png") or "💬"
HEADER_LOGO_DATA_URI = get_image_data_uri("homeai_logo@2x.png")

# -----------------------------------------------
# Streamlit page configuration
# -----------------------------------------------
st.set_page_config(
    page_title="HomeAI",
    page_icon=PAGE_ICON,
    layout="centered",
)


# -----------------------------------------------
# 1. Model initialization
# -----------------------------------------------
@st.cache_resource
def get_model():
    """Initialize model with caching

    Switch between OpenAI and local LLM using USE_LOCAL_LLM environment variable:
    - USE_LOCAL_LLM=true: Local LLM (default)
    - USE_LOCAL_LLM=false: OpenAI API (optional)
    """
    if USE_LOCAL_LLM:
        # Local LLM (LM Studio, llama.cpp, etc.)
        return ChatOpenAI(
            base_url=LOCAL_LLM_BASE_URL,
            api_key="dummy",  # Not required for local LLM
            model=LOCAL_LLM_MODEL,
            temperature=0.7,
        )
    else:
        # OpenAI API
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Please check your .env file.")
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
        )


# -----------------------------------------------
# 2. Prompt template definition
# -----------------------------------------------
@st.cache_resource
def get_prompt():
    """Initialize prompt template with caching"""
    return PromptTemplates.create_prompt_template(LANGUAGE)


# -----------------------------------------------
# 3. LCEL chain construction
# -----------------------------------------------
@st.cache_resource
def get_chain():
    """Initialize chain with caching"""
    model = get_model()
    prompt = get_prompt()
    return prompt | model | StrOutputParser()


# -----------------------------------------------
# 4. Conversation history (Memory) setup
# -----------------------------------------------
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Return history object linked to session ID (create new if not exists)"""
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = InMemoryChatMessageHistory()
    return st.session_state.store[session_id]


def get_chain_with_history():
    """Get chain with history management"""
    chain = get_chain()
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


# -----------------------------------------------
# 5. Streamlit UI
# -----------------------------------------------
def main():
    # Initialize session state
    if "store" not in st.session_state:
        st.session_state.store = {}
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Get UI labels based on current language
    ui_labels = PromptTemplates.get_ui_labels()
    labels = ui_labels.get(LANGUAGE, ui_labels["en"])

    # Header
    if HEADER_LOGO_DATA_URI is not None:
        st.markdown(
            f"""
            <h1 style="display: flex; align-items: center; gap: 0.5rem;">
                <img src="{HEADER_LOGO_DATA_URI}" alt="Home AI" style="width: 56px; height: 56px;">
                <span>{labels["title"]}</span>
            </h1>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title(f"💬 {labels['title']}")
    st.caption(labels["caption"])

    # Sidebar: Settings
    with st.sidebar:
        st.header(labels["settings"])

        # Language selection
        available_languages = PromptTemplates.get_available_languages()
        selected_language = st.selectbox(
            labels["language"],
            options=list(available_languages.keys()),
            format_func=lambda x: available_languages[x],
            index=list(available_languages.keys()).index(LANGUAGE),
            help=labels["language_help"],
        )

        # Update language if changed
        if selected_language != LANGUAGE:
            os.environ["LANGUAGE"] = selected_language
            st.rerun()

        # Session management
        session_id = st.text_input(
            labels["session_id"],
            value="default-session",
            help=labels["session_id_help"],
        )

        # Clear history button
        if st.button(labels["clear_history"], type="secondary"):
            st.session_state.messages = []
            st.session_state.store = {}
            st.rerun()

        # Model information
        st.divider()
        st.subheader(labels["model_info"])

        # Language info
        st.info(
            f"{labels['language_info']}: {available_languages.get(selected_language, selected_language)}"
        )
        if USE_LOCAL_LLM:
            st.code(
                f"Local LLM\nURL: {LOCAL_LLM_BASE_URL}\nModel: {LOCAL_LLM_MODEL}\ntemperature=0.7"
            )
        else:
            st.code("OpenAI API\nModel: gpt-4o-mini\ntemperature=0.7")

    # Display message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input(labels["input_placeholder"]):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner(labels["thinking"]):
                chain_with_history = get_chain_with_history()
                response = chain_with_history.invoke(
                    {"input": prompt},
                    config={"configurable": {"session_id": session_id}},
                )
                st.markdown(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
            Home AI | Python + Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
