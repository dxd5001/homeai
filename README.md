# HomeAI

A home AI assistant built with LangChain. **Primarily uses local LLMs** with OpenAI as an optional provider.

## Structure

```
.
├── chatbot.py        # CLI chatbot with multi-language support
├── web_chatbot.py    # Streamlit web interface
├── prompts.py        # Multi-language prompt templates
├── requirements.txt  # Dependencies
├── .env.example      # Environment configuration
├── .gitignore
└── README.md
```

## Setup

### 1. Clone repository

```bash
git clone https://github.com/dxd5001/homeai.git
cd homeai
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy `.env.example` to `.env` and configure it.

```bash
cp .env.example .env
```

**Note**: `.env` contains your actual API keys and settings, while `.env.example` is the template. The `.env` file is automatically excluded from Git by `.gitignore`.

Edit `.env`:

```bash
# Use local LLM (default)
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=your-model-name

# Use OpenAI (optional)
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
# USE_LOCAL_LLM=false
```

### 5. Run

```bash
python chatbot.py
```

## Usage

```
==================================================
  HomeAI
  Type 'quit' or 'exit' to end
==================================================

You: Hello!
AI : Hello! How can I help you today?

You: What is LangChain?
AI : LangChain is a framework for building applications with large language models...

You: quit
Ending conversation. See you again!
```

## Code Structure (Learning Points)

| Step | Class / Function | Role |
|---|---|---|
| 1 | `ChatOpenAI` / `ChatLocalAI` | LLM model initialization (local/OpenAI switching) |
| 2 | `ChatPromptTemplate` | System prompt + history template definition |
| 3 | `prompt \| model \| StrOutputParser()` | LCEL chain construction |
| 4 | `InMemoryChatMessageHistory` | In-memory conversation history management |
| 5 | `RunnableWithMessageHistory` | Add history management to chain |

## Future Extension Ideas

- [ ] Allow system prompt changes via command line arguments
- [ ] Save/load conversation history to/from files (JSON)
- [ ] RAG (Retrieval-Augmented Generation): Reference documents like PDFs for answers
- [ ] Create Web API with FastAPI for frontend integration
- [ ] Visualize traces and debugging with LangSmith
- [ ] Build more complex agents with LangGraph
- [ ] Add local LLM model management features
- [ ] Support multiple local LLM providers (Ollama, llama.cpp, etc.)

---

## 🌐 Remote Access

When using local LLMs (LM Studio, llama.cpp), you can access your HomeAI remotely from your smartphone using Tailscale Serve for private access within your Tailnet.

### Prerequisites

1. **Tailscale account**: Register at https://tailscale.com
2. **Tailscale client**: Install on home PC and smartphone
3. **Local LLM (LM Studio, etc.)**: Running in API server mode

### Setup Steps

#### 1. Start local LLM

**For LM Studio:**
1. Launch LM Studio
2. Enable server mode
3. Check port (default: 1234)

#### 2. Configure .env file

```bash
# Use local LLM (default settings)
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://127.0.0.1:1235/v1  # Change to your LM Studio port
LOCAL_LLM_MODEL=google/gemma-4-e4b  # Change to your actual model name

# Use OpenAI (optional)
# USE_LOCAL_LLM=false
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

#### 3. Launch Streamlit app

```bash
source venv/bin/activate
streamlit run web_chatbot.py
```

#### 4. Expose with Tailscale Serve

```bash
tailscale serve --bg 8501
```

Now accessible at `https://your-tailnet-name.ts.net` within your Tailnet.

#### 5. Access from smartphone

1. Install Tailscale app on smartphone
2. Login with same account
3. Access Serve URL in browser

### Security

- **Private access**: Only Tailnet members can access (not publicly accessible)
- **HTTPS**: Serve automatically provides HTTPS with valid certificates
- **Authentication**: Tailscale authentication as first layer of security
- **Access control**: ACL (Access Control Lists) for fine-grained permissions

### Architecture

```
Smartphone (remote)
    ↓ Tailscale VPN
Tailscale Serve
    ↓ Private communication
Home PC
    ↓ localhost
Streamlit → Local LLM
```
