# Requirements Document

## Introduction

This document specifies the requirements for restructuring the Home AI project into a
well-defined, layered architecture with a clear separation of concerns between two
distinct components:

- **Home AI** — an open-source, general-purpose local LLM wrapper and home AI
  foundation. It provides the LLM client abstraction, chat session management, prompt
  management, configuration, and optional API/web surfaces. It must remain generic and
  contain no user-specific personal data, private workflows, or Obsidian Vault logic.

- **Orb** — a higher-level personal assistant application built on top of Home AI. It
  may include Obsidian Vault RAG, long-term memory, location/context awareness,
  proactive assistance, personal workflows, and mobile sub-agent integration.

The restructuring is phased to avoid breaking the current working Web Launcher while
progressively extracting a reusable core, adding a FastAPI server, updating the
launcher, and preparing the Orb integration boundary.

---

## Glossary

- **Home_AI**: The open-source local LLM wrapper project and its runtime components.
- **homeai-core**: The extracted Python package containing LLM client abstraction,
  prompt management, chat session management, conversation history, config management,
  and interface definitions (retriever, memory, tool, agent).
- **homeai-api**: The FastAPI server component exposing HTTP endpoints for chat,
  health, model listing, and configuration.
- **homeai-web**: The Streamlit web UI component.
- **homeai-launcher**: The Pystray system tray launcher component.
- **Desktop_App**: The experimental PyQt6 native desktop application.
- **Orb**: The personal assistant application built on top of Home AI or homeai-core.
- **LLM_Client**: The abstraction layer over OpenAI-compatible API endpoints.
- **Config_Manager**: The component responsible for reading, writing, and validating
  application configuration.
- **Prompt_Manager**: The component responsible for managing multi-language system
  prompts and UI labels.
- **Chat_Session**: A stateful conversation context identified by a session ID,
  containing conversation history.
- **Tailscale_Serve**: The Tailscale CLI feature that exposes a local port over a
  private Tailnet with HTTPS.
- **OpenAI_Compatible_API**: An HTTP API that follows the OpenAI REST API schema,
  supported by LM Studio, Ollama, llama.cpp, vLLM, and OpenAI itself.
- **Orb_Extension_Boundary**: The defined interface through which Orb integrates with
  Home AI without coupling to its internals.
- **PyInstaller**: The tool used to package Python applications into standalone
  executables or application bundles.

---

## Requirements

---

### REQ-001: OpenAI-Compatible LLM Support

**User Story:** As a user, I want Home AI to connect to any OpenAI-compatible local
LLM server, so that I can use LM Studio, Ollama, llama.cpp, vLLM, or the OpenAI API
interchangeably without changing application code.

#### Acceptance Criteria

1. THE LLM_Client SHALL accept a `base_url`, `api_key`, and `model` parameter to
   connect to any OpenAI-compatible endpoint.
2. WHEN `USE_LOCAL_LLM` is `true`, THE LLM_Client SHALL connect to the configured
   `LOCAL_LLM_BASE_URL` using a placeholder API key.
3. WHEN `USE_LOCAL_LLM` is `false`, THE LLM_Client SHALL connect to the OpenAI API
   using the configured `OPENAI_API_KEY`.
4. IF `USE_LOCAL_LLM` is `false` and `OPENAI_API_KEY` is empty, THEN THE LLM_Client
   SHALL raise a configuration error before attempting any LLM call.
5. THE LLM_Client SHALL support the following local LLM servers via their
   OpenAI-compatible `/v1` endpoints: LM Studio, Ollama, llama.cpp, and vLLM.
6. THE LLM_Client SHALL NOT contain any logic specific to a single LLM provider beyond
   the `base_url` and `api_key` parameters.

---

### REQ-002: homeai-core Package Extraction

**User Story:** As a developer, I want the shared LLM, prompt, session, and config
logic extracted into a `homeai-core` Python package, so that all Home AI components
and Orb can import it without duplicating code.

#### Acceptance Criteria

1. THE homeai-core SHALL be structured as an importable Python package installable via
   `pip install -e .` from the repository root.
2. THE homeai-core SHALL expose the following modules: `llm_client`, `prompt_manager`,
   `chat_session`, `config_manager`, and interface definitions for `retriever`,
   `memory`, `tool`, and `agent`.
3. THE homeai-core SHALL NOT import from `homeai-api`, `homeai-web`, `homeai-launcher`,
   or `Desktop_App` modules.
4. THE homeai-core SHALL NOT contain any Obsidian Vault logic, personal data, or
   private workflow code.
5. WHEN homeai-core is imported, THE homeai-core SHALL NOT start any server, open any
   port, or launch any subprocess.
6. THE homeai-core SHALL provide a `LLMClient` class that wraps `langchain_openai
   .ChatOpenAI` and is constructable from a `Config_Manager` instance.
7. THE homeai-core SHALL provide a `ChatSession` class that manages
   `InMemoryChatMessageHistory` keyed by session ID.
8. THE homeai-core SHALL provide a `PromptManager` class that encapsulates the
   multi-language system prompts and UI labels currently in `prompts.py`.

---

### REQ-003: Unified Configuration Management

**User Story:** As a developer, I want a single Config_Manager in homeai-core that
works for all components, so that configuration is consistent across the web UI,
API server, launcher, and desktop app.

#### Acceptance Criteria

1. THE Config_Manager SHALL support loading configuration from a `.env` file, a JSON
   config file, and environment variables, with environment variables taking highest
   precedence.
2. THE Config_Manager SHALL expose the following configuration keys: `use_local_llm`,
   `local_llm_base_url`, `local_llm_model`, `openai_api_key`, `language`, `auto_start`,
   and `first_run`.
3. WHEN a configuration key is missing from all sources, THE Config_Manager SHALL use
   the defined default value for that key.
4. THE Config_Manager SHALL persist mutable configuration to `~/.homeai/config.json`.
5. IF the config file is malformed or unreadable, THEN THE Config_Manager SHALL fall
   back to default values and log a warning.
6. THE Config_Manager SHALL NOT store `openai_api_key` in plain text in any file that
   is committed to version control.

---

### REQ-004: Streamlit Web UI Preservation

**User Story:** As a user, I want the existing Streamlit web UI to continue working
without regression after the refactoring, so that my current workflow is not disrupted.

#### Acceptance Criteria

1. WHEN `web_chatbot.py` is run via `streamlit run web_chatbot.py`, THE homeai-web
   SHALL start and serve the chat UI on `http://localhost:8501`.
2. THE homeai-web SHALL support multi-language UI labels for Japanese, English,
   Chinese, Simplified; Spanish, and French.
3. THE homeai-web SHALL display the current LLM provider, model name, and base URL in
   the sidebar.
4. WHEN the user clears conversation history, THE homeai-web SHALL reset the in-memory
   session store and re-render the empty chat view.
5. WHEN the user changes the language selector, THE homeai-web SHALL update the system
   prompt language and re-render the UI in the selected language.
6. THE homeai-web SHALL use homeai-core for LLM client initialization, prompt
   management, and chat session management after the core extraction.

---

### REQ-005: FastAPI Server Introduction

**User Story:** As a developer or external client, I want a FastAPI server that exposes
Home AI over HTTP, so that Orb and other clients can interact with Home AI via a
well-defined REST API without embedding the Python core directly.

#### Acceptance Criteria

1. THE homeai-api SHALL expose a `GET /health` endpoint that returns HTTP 200 with a
   JSON body indicating service status.
2. THE homeai-api SHALL expose a `POST /chat` endpoint that accepts a JSON body with
   `session_id` and `message` fields and returns the AI response as a JSON string.
3. THE homeai-api SHALL expose a `GET /models` endpoint that returns the currently
   configured LLM provider, base URL, and model name.
4. THE homeai-api SHALL expose a `GET /config` endpoint that returns non-sensitive
   configuration values; `openai_api_key` SHALL be omitted or masked in the response.
5. THE homeai-api SHALL expose a `POST /chat/stream` endpoint that returns the AI
   response as a server-sent events stream.
6. THE homeai-api SHALL use homeai-core for all LLM calls, prompt management, and
   session management.
7. WHEN the homeai-api is started, THE homeai-api SHALL NOT break or interfere with a
   concurrently running homeai-web instance.
8. THE homeai-api SHALL be startable independently of homeai-web and homeai-launcher.
9. IF a request to `POST /chat` or `POST /chat/stream` is made while the LLM server is
   unreachable, THEN THE homeai-api SHALL return HTTP 503 with a descriptive error
   message.

---

### REQ-006: Launcher Behavior

**User Story:** As a user, I want the system tray launcher to manage the lifecycle of
the web UI and optionally the API server, so that I can start, stop, and access Home
AI from the menu bar without using a terminal.

#### Acceptance Criteria

1. WHEN the homeai-launcher is started, THE homeai-launcher SHALL start the
   homeai-web Streamlit process if it is not already running on the configured port.
2. WHEN the Streamlit process is ready to accept connections, THE homeai-launcher SHALL
   open the default browser to `http://localhost:8501`.
3. THE homeai-launcher SHALL provide a system tray menu with the following items: Open
   Home AI, Start Tailscale Serve, Stop Tailscale Serve, Show Tailscale Status,
   Tailscale Serve Help, and Quit.
4. WHEN the user selects Quit from the tray menu, THE homeai-launcher SHALL terminate
   the Streamlit subprocess and exit the launcher process.
5. THE homeai-launcher SHALL write timestamped log entries to
   `~/.homeai/logs/web_launcher.log`.
6. WHEN the log file exceeds 1 MB, THE homeai-launcher SHALL rotate it to
   `web_launcher.log.1` before writing new entries.
7. THE homeai-launcher SHALL support execution as a PyInstaller-packaged application
   bundle on macOS and Windows.
8. WHEN packaged with PyInstaller, THE homeai-launcher SHALL locate `web_chatbot.py`
   and `prompts.py` relative to the bundle's resource path.

---

### REQ-007: Tailscale Serve Integration

**User Story:** As a user, I want to expose Home AI over my private Tailnet using
Tailscale Serve, so that I can access it securely from my smartphone without opening
public ports.

#### Acceptance Criteria

1. THE homeai-launcher SHALL search for the Tailscale CLI in the following locations in
   order: `/usr/local/bin/tailscale`, `/opt/homebrew/bin/tailscale`,
   `/Applications/Tailscale.app/Contents/MacOS/Tailscale`, `/usr/bin/tailscale`, and
   the system `PATH`.
2. WHEN the user selects Start Tailscale Serve, THE homeai-launcher SHALL run
   `tailscale serve --bg <PORT>` for the configured Streamlit port.
3. WHEN the user selects Stop Tailscale Serve, THE homeai-launcher SHALL run
   `tailscale serve reset`.
4. WHEN the user selects Show Tailscale Status, THE homeai-launcher SHALL run
   `tailscale serve status` and write the output to the launcher log.
5. IF the Tailscale CLI is not found, THEN THE homeai-launcher SHALL open the Tailscale
   Serve documentation URL in the default browser.
6. IF the Tailscale command output contains "Tailscale GUI failed to start", THEN THE
   homeai-launcher SHALL log a warning and open the Tailscale Serve documentation URL.

---

### REQ-008: Orb Extension Boundary

**User Story:** As an Orb developer, I want a clearly defined interface through which
Orb can extend Home AI with personal assistant features, so that Orb remains decoupled
from Home AI internals and Home AI remains generic.

#### Acceptance Criteria

1. THE homeai-core SHALL define abstract interface classes for `RetrieverInterface`,
   `MemoryInterface`, `ToolInterface`, and `AgentInterface` that Orb can implement.
2. THE homeai-core SHALL NOT import from any Orb module or repository.
3. THE Orb SHALL integrate with Home AI exclusively through homeai-core interfaces or
   the homeai-api HTTP endpoints.
4. THE homeai-core SHALL NOT contain any reference to Obsidian, personal vault paths,
   private note content, or user-specific workflow logic.
5. WHERE an `AgentInterface` implementation is provided, THE homeai-core SHALL invoke
   it in place of the default LLM_Client chain for chat session processing.
6. THE homeai-api SHALL accept an optional `agent_id` parameter on `POST /chat` and
   `POST /chat/stream` to route requests to a registered agent implementation.

---

### REQ-009: Obsidian RAG Boundary

**User Story:** As a Home AI maintainer, I want to ensure that Obsidian Vault RAG and
personal knowledge retrieval logic lives exclusively in Orb, so that the Home AI
open-source repository remains free of private data and personal workflows.

#### Acceptance Criteria

1. THE homeai-core SHALL NOT contain any file path, import, or configuration key
   referencing an Obsidian Vault.
2. THE homeai-api SHALL NOT contain any endpoint or handler that reads from a local
   file system path configured as an Obsidian Vault.
3. THE homeai-web SHALL NOT contain any UI element or configuration option for
   Obsidian Vault path configuration.
4. THE homeai-launcher SHALL NOT contain any logic for indexing, reading, or watching
   an Obsidian Vault directory.
5. WHERE Obsidian RAG is required, THE Orb SHALL implement the `RetrieverInterface`
   defined in homeai-core and inject it at runtime.

---

### REQ-010: Cross-Platform Packaging

**User Story:** As a user, I want to install Home AI as a native application bundle on
macOS and Windows, so that I do not need to manage a Python environment manually.

#### Acceptance Criteria

1. THE homeai-launcher SHALL be packageable into a macOS `.app` bundle using
   PyInstaller with the `--windowed --onedir` flags.
2. THE homeai-launcher SHALL be packageable into a Windows `.exe` using PyInstaller
   with the `--windowed --onedir` flags.
3. WHEN packaged, THE homeai-launcher SHALL include `web_chatbot.py`, `prompts.py`,
   and all Streamlit assets required for the web UI to function.
4. WHEN packaged, THE homeai-launcher SHALL collect all Streamlit package data using
   `--collect-all streamlit` and include the `streamlit.web.cli` hidden import.
5. THE Desktop_App SHALL be packageable into a macOS `.app` bundle using PyInstaller
   with the `--windowed --onedir` flags.
6. WHEN packaged as a macOS `.app`, THE homeai-launcher SHALL read configuration and
   write logs to paths within `~/Library/Application Support/HomeAI/` or
   `~/.homeai/` to comply with macOS sandboxing conventions.

---

### REQ-011: Auto-Start on System Boot

**User Story:** As a user, I want Home AI to start automatically when I log in, so
that it is always available without manual intervention.

#### Acceptance Criteria

1. THE homeai-launcher SHALL support enabling auto-start on macOS by creating a launchd
   plist in `~/Library/LaunchAgents/`.
2. THE homeai-launcher SHALL support enabling auto-start on Windows by writing a
   registry entry under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
3. THE homeai-launcher SHALL support enabling auto-start on Linux by creating a systemd
   user service file in `~/.config/systemd/user/`.
4. WHEN auto-start is disabled by the user, THE homeai-launcher SHALL remove the
   platform-specific auto-start entry created in criteria 1, 2, or 3.
5. THE Config_Manager SHALL persist the `auto_start` preference to
   `~/.homeai/config.json`.

---

### REQ-012: Phased Implementation Plan

**User Story:** As a project maintainer, I want the restructuring to proceed in
well-defined phases, so that the current working Web Launcher is never broken during
the transition.

#### Acceptance Criteria

1. THE Home_AI project SHALL implement the restructuring in the following phases in
   order: Phase 1 Stabilize, Phase 2 Extract Core, Phase 3 Add FastAPI, Phase 4 Update
   Launcher, Phase 5 Prepare Orb Integration, Phase 6 Packaging and Release.
2. WHILE Phase 1 is active, THE homeai-web and homeai-launcher SHALL remain fully
   functional with no regressions to existing behavior.
3. WHEN Phase 2 is complete, THE homeai-core package SHALL be importable and all
   existing components SHALL use it in place of their inline LLM, prompt, and session
   logic.
4. WHEN Phase 3 is complete, THE homeai-api SHALL be startable independently and SHALL
   pass all REQ-005 acceptance criteria.
5. WHEN Phase 4 is complete, THE homeai-launcher SHALL optionally start homeai-api
   alongside homeai-web and SHALL pass all REQ-006 acceptance criteria.
6. WHEN Phase 5 is complete, THE homeai-core SHALL expose all interface definitions
   required by REQ-008 and REQ-009.
7. WHEN Phase 6 is complete, THE homeai-launcher and Desktop_App SHALL be packageable
   per REQ-010 and produce working application bundles on macOS and Windows.
