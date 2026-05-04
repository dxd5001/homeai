"""
HomeAI - LangChain Simple Chatbot
=================================
How to run:
    python chatbot.py

To exit:
    "quit" or "exit" or Ctrl+C
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from prompts import PromptTemplates

# Load environment variables from .env file
load_dotenv()

# Get environment variables
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "local-model")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LANGUAGE = os.getenv("LANGUAGE", "ja")  # Default to Japanese

# -----------------------------------------------
# 1. Model initialization
#    - Switch between OpenAI and local LLM using USE_LOCAL_LLM environment variable
#    - USE_LOCAL_LLM=true: Local LLM (default)
#    - USE_LOCAL_LLM=false: OpenAI API (optional)
# -----------------------------------------------
if USE_LOCAL_LLM:
    # Local LLM (LM Studio, llama.cpp, etc.)
    model = ChatOpenAI(
        base_url=LOCAL_LLM_BASE_URL,
        api_key="dummy",  # Not required for local LLM
        model=LOCAL_LLM_MODEL,
        temperature=0.7,
    )
    print(f"🤖 Using local LLM: {LOCAL_LLM_MODEL}")
else:
    # OpenAI API
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Please check your .env file.")
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
    )
    print("🌐 Using OpenAI API: gpt-4o-mini")

# -----------------------------------------------
# 2. Prompt template definition
#    - system  : Define AI role and constraints
#    - MessagesPlaceholder : Place where conversation history is inserted
# -----------------------------------------------
prompt = PromptTemplates.create_prompt_template(LANGUAGE)

# Display language info
print(
    f"🌐 Language: {PromptTemplates.get_available_languages().get(LANGUAGE, LANGUAGE)}"
)

# -----------------------------------------------
# 3. LCEL chain construction
#    Connect prompt | model | parser in order with pipes
#    Convert AIMessage → str with StrOutputParser
# -----------------------------------------------
chain = prompt | model | StrOutputParser()

# -----------------------------------------------
# 4. Conversation history (Memory) setup
#    Maintain InMemoryChatMessageHistory for each session ID
#    Note: History is reset when process ends
# -----------------------------------------------
store: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Return history object linked to session ID (create new if not exists)"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# Add history management to chain with RunnableWithMessageHistory
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


# -----------------------------------------------
# 5. Conversation loop
# -----------------------------------------------
def main():
    print("=" * 50)
    print("  HomeAI")
    if USE_LOCAL_LLM:
        print(f"  Local LLM: {LOCAL_LLM_MODEL}")
    else:
        print("  OpenAI API: gpt-4o-mini")
    print(
        f"  Language: {PromptTemplates.get_available_languages().get(LANGUAGE, LANGUAGE)}"
    )
    print("  Type 'quit' or 'exit' to end")
    print("=" * 50)
    print()

    # Session ID (change here for multiple users)
    session_id = "default-session"

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "終了"):
            print("Ending conversation. See you again!")
            break

        # Call the chain
        # Identify history by session_id in config
        response = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        print(f"AI : {response}")
        print()


if __name__ == "__main__":
    main()
