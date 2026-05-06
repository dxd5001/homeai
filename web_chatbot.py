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
from config_manager import ConfigManager
from prompts import PromptTemplates
from version import APP_VERSION

# Load environment variables from .env file
load_dotenv()

CONFIG_MANAGER = ConfigManager()


def get_config_value(key: str, env_key: str, default):
    """Return configuration value with environment fallback."""
    env_value = os.getenv(env_key)
    if env_value is not None and CONFIG_MANAGER.is_first_run():
        return env_value
    return CONFIG_MANAGER.get(key, default)


def get_bool_config_value(key: str, env_key: str, default: bool) -> bool:
    """Return boolean configuration value with environment fallback."""
    value = get_config_value(key, env_key, default)
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


USE_LOCAL_LLM = get_bool_config_value(
    "use_local_llm",
    "USE_LOCAL_LLM",
    ConfigManager.DEFAULT_CONFIG["use_local_llm"],
)
LOCAL_LLM_BASE_URL = get_config_value(
    "local_llm_base_url",
    "LOCAL_LLM_BASE_URL",
    ConfigManager.DEFAULT_CONFIG["local_llm_base_url"],
)
LOCAL_LLM_MODEL = get_config_value(
    "local_llm_model",
    "LOCAL_LLM_MODEL",
    ConfigManager.DEFAULT_CONFIG["local_llm_model"],
)
OPENAI_API_KEY = get_config_value(
    "openai_api_key",
    "OPENAI_API_KEY",
    ConfigManager.DEFAULT_CONFIG["openai_api_key"],
)
LANGUAGE = get_config_value(
    "language", "LANGUAGE", ConfigManager.DEFAULT_CONFIG["language"]
)


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


def save_web_settings(
    selected_language: str,
    use_local_llm: bool,
    local_llm_base_url: str,
    local_llm_model: str,
    openai_api_key: str,
) -> None:
    """Save web UI settings and reload cached resources."""
    CONFIG_MANAGER.update(
        {
            "language": selected_language,
            "use_local_llm": use_local_llm,
            "local_llm_base_url": local_llm_base_url,
            "local_llm_model": local_llm_model,
            "openai_api_key": openai_api_key,
            "first_run": False,
        }
    )
    get_model.clear()
    get_prompt.clear()
    get_chain.clear()
    st.rerun()


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
            CONFIG_MANAGER.set("language", selected_language)
            CONFIG_MANAGER.mark_first_run_complete()
            st.rerun()

        st.divider()
        st.subheader("LLM Settings")
        llm_provider = st.radio(
            "Provider",
            options=["Local LLM", "OpenAI API"],
            index=0 if USE_LOCAL_LLM else 1,
            horizontal=True,
        )
        selected_use_local_llm = llm_provider == "Local LLM"
        settings_local_llm_base_url = st.text_input(
            "Local LLM Base URL",
            value=LOCAL_LLM_BASE_URL,
            help="Example: http://127.0.0.1:1235/v1",
            disabled=not selected_use_local_llm,
        )
        settings_local_llm_model = st.text_input(
            "Local LLM Model",
            value=LOCAL_LLM_MODEL,
            help="Use the model name shown by your local LLM server.",
            disabled=not selected_use_local_llm,
        )
        settings_openai_api_key = st.text_input(
            "OpenAI API Key",
            value=OPENAI_API_KEY,
            type="password",
            disabled=selected_use_local_llm,
        )
        if st.button("Save LLM Settings", type="primary"):
            save_web_settings(
                selected_language,
                selected_use_local_llm,
                settings_local_llm_base_url.strip(),
                settings_local_llm_model.strip(),
                settings_openai_api_key.strip(),
            )

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

        st.divider()
        st.caption(f"Home AI v{APP_VERSION}")

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
