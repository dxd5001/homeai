"""
HomeAI Web Launcher
===================
Pystray-based launcher for the Streamlit web UI.
"""

import os
import shlex
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

APP_NAME = "Home AI Launcher"
HOST = "127.0.0.1"
PORT = 8501
URL = f"http://localhost:{PORT}"
STARTUP_TIMEOUT_SECONDS = 30
STREAMLIT_CHILD_ARG = "--streamlit-child"
MAX_LOG_SIZE_BYTES = 1_000_000
TAILSCALE_CANDIDATE_PATHS = [
    "/usr/local/bin/tailscale",
    "/opt/homebrew/bin/tailscale",
    "/usr/bin/tailscale",
]
TAILSCALE_APP_PATH = Path("/Applications/Tailscale.app")
TAILSCALE_CLI_INSTALL_SCRIPT_PATH = (
    TAILSCALE_APP_PATH / "Contents" / "Resources" / "InstallTailscaleCLI.scpt"
)
TAILSCALE_APP_BINARY_PATH = TAILSCALE_APP_PATH / "Contents" / "MacOS" / "Tailscale"
TAILSCALE_CLI_WRAPPER_PATH = Path("/usr/local/bin/tailscale")

streamlit_process = None
tray_icon = None


def get_base_path() -> Path:
    """Return base path for both source and PyInstaller bundle execution."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_web_chatbot_path() -> Path:
    """Return the Streamlit application path."""
    return get_base_path() / "web_chatbot.py"


def get_tray_icon_path() -> Path:
    """Return the tray icon image path."""
    return get_base_path() / "static" / "homeai_icon-8.png"


def get_log_path() -> Path:
    """Return launcher log file path."""
    log_dir = Path.home() / ".homeai" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "web_launcher.log"


def rotate_log_if_needed(log_path: Path) -> None:
    """Rotate the launcher log when it exceeds the maximum size."""
    if not log_path.exists() or log_path.stat().st_size <= MAX_LOG_SIZE_BYTES:
        return

    rotated_log_path = log_path.with_name(f"{log_path.name}.1")
    if rotated_log_path.exists():
        rotated_log_path.unlink()
    log_path.rename(rotated_log_path)


def write_log(message: str) -> None:
    """Write a message to the launcher log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_path = get_log_path()
    rotate_log_if_needed(log_path)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def is_port_open(host: str, port: int) -> bool:
    """Check whether the Streamlit server port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_streamlit() -> bool:
    """Wait until Streamlit is ready or timeout is reached."""
    deadline = time.time() + STARTUP_TIMEOUT_SECONDS
    while time.time() < deadline:
        if is_port_open(HOST, PORT):
            return True
        time.sleep(0.5)
    return False


def create_icon_image() -> Image.Image:
    """Create a simple tray icon image."""
    tray_icon_path = get_tray_icon_path()
    if tray_icon_path.exists():
        return Image.open(tray_icon_path).convert("RGBA")

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(37, 99, 235, 255))
    draw.text((20, 20), "AI", fill=(255, 255, 255, 255))
    return image


def start_streamlit() -> None:
    """Start Streamlit server if it is not already running."""
    global streamlit_process

    if is_port_open(HOST, PORT):
        write_log(f"Streamlit is already running at {URL}")
        return

    web_chatbot_path = get_web_chatbot_path()
    write_log(f"Starting Streamlit with app path: {web_chatbot_path}")
    if getattr(sys, "frozen", False):
        command = [sys.executable, STREAMLIT_CHILD_ARG, str(web_chatbot_path)]
    else:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            STREAMLIT_CHILD_ARG,
            str(web_chatbot_path),
        ]

    write_log(f"Streamlit command: {' '.join(command)}")
    log_file = open(get_log_path(), "a", encoding="utf-8")
    streamlit_process = subprocess.Popen(
        command,
        cwd=str(get_base_path()),
        env={
            **os.environ,
            "HOMEAI_STREAMLIT_CHILD": "1",
        },
        stdout=log_file,
        stderr=log_file,
    )
    write_log(f"Streamlit process started with PID: {streamlit_process.pid}")


def open_home_ai() -> None:
    """Open Home AI Web UI in the default browser."""
    webbrowser.open(URL)


def show_tailscale_help() -> None:
    """Open Tailscale Serve documentation."""
    webbrowser.open("https://tailscale.com/kb/1312/serve")


def show_tailscale_download() -> None:
    """Open Tailscale download page."""
    webbrowser.open("https://tailscale.com/download/mac")


def quote_applescript_string(value: str) -> str:
    """Quote a string for AppleScript source."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def find_tailscale_command() -> str | None:
    """Find the Tailscale command path."""
    for candidate_path in TAILSCALE_CANDIDATE_PATHS:
        if Path(candidate_path).exists():
            return candidate_path
    return shutil.which("tailscale")


def install_tailscale_cli() -> bool:
    """Install the Tailscale CLI using the official bundled installer."""
    if not TAILSCALE_APP_PATH.exists():
        write_log("Tailscale app not found at /Applications/Tailscale.app.")
        show_tailscale_download()
        return False

    if not TAILSCALE_CLI_INSTALL_SCRIPT_PATH.exists():
        write_log(
            f"Tailscale CLI installer not found: {TAILSCALE_CLI_INSTALL_SCRIPT_PATH}"
        )
        show_tailscale_help()
        return False

    write_log(f"Running Tailscale CLI installer: {TAILSCALE_CLI_INSTALL_SCRIPT_PATH}")
    result = subprocess.run(
        ["osascript", str(TAILSCALE_CLI_INSTALL_SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    write_log(f"Tailscale CLI installer return code: {result.returncode}")
    if result.stdout:
        write_log(f"Tailscale CLI installer stdout: {result.stdout.strip()}")
    if result.stderr:
        write_log(f"Tailscale CLI installer stderr: {result.stderr.strip()}")

    if result.returncode == 0 and find_tailscale_command() is not None:
        write_log("Tailscale CLI installed successfully.")
        return True

    write_log("Tailscale CLI installer did not make a usable CLI command available.")
    if install_tailscale_cli_wrapper():
        return True

    show_tailscale_help()
    return False


def install_tailscale_cli_wrapper() -> bool:
    """Install a Tailscale CLI wrapper when the bundled installer fails."""
    if not TAILSCALE_APP_BINARY_PATH.exists():
        write_log(f"Tailscale app binary not found: {TAILSCALE_APP_BINARY_PATH}")
        return False

    wrapper_script = f'#!/bin/sh\nexec {TAILSCALE_APP_BINARY_PATH} "$@"\n'
    shell_command = (
        "mkdir -p /usr/local/bin && "
        f"printf %s {shlex.quote(wrapper_script)} > {TAILSCALE_CLI_WRAPPER_PATH} && "
        f"chmod +x {TAILSCALE_CLI_WRAPPER_PATH}"
    )
    result = subprocess.run(
        [
            "osascript",
            "-e",
            f"do shell script {quote_applescript_string(shell_command)} with administrator privileges",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    write_log(f"Tailscale CLI wrapper installer return code: {result.returncode}")
    if result.stdout:
        write_log(f"Tailscale CLI wrapper installer stdout: {result.stdout.strip()}")
    if result.stderr:
        write_log(f"Tailscale CLI wrapper installer stderr: {result.stderr.strip()}")

    if result.returncode == 0 and find_tailscale_command() is not None:
        write_log("Tailscale CLI wrapper installed successfully.")
        return True

    write_log(
        "Tailscale CLI wrapper installer did not make a usable CLI command available."
    )
    return False


def run_tailscale_command(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a Tailscale command and write the result to the launcher log."""
    tailscale_command = find_tailscale_command()
    if tailscale_command is None:
        write_log("Tailscale CLI command not found. Trying to install it.")
        if not install_tailscale_cli():
            return None
        tailscale_command = find_tailscale_command()
        if tailscale_command is None:
            write_log(
                "Tailscale CLI command is still not available after installation."
            )
            return None

    command = [tailscale_command, *args]
    write_log(f"Tailscale command: {' '.join(command)}")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    write_log(f"Tailscale return code: {result.returncode}")
    if result.stdout:
        write_log(f"Tailscale stdout: {result.stdout.strip()}")
    if result.stderr:
        write_log(f"Tailscale stderr: {result.stderr.strip()}")
    if "Tailscale GUI failed to start" in result.stdout:
        write_log("Detected Tailscale app binary instead of a usable CLI command.")
    return result


def is_tailscale_gui_error(result: subprocess.CompletedProcess[str] | None) -> bool:
    """Return whether the Tailscale command failed as a GUI launch."""
    if result is None:
        return True
    return "Tailscale GUI failed to start" in result.stdout


def show_tailscale_status() -> None:
    """Log current Tailscale Serve status."""
    run_tailscale_command(["serve", "status"])


def start_tailscale_serve() -> None:
    """Start Tailscale Serve for the Streamlit port."""
    status_result = run_tailscale_command(["serve", "status"])
    if is_tailscale_gui_error(status_result):
        write_log("Tailscale Serve start skipped because Tailscale CLI is not usable.")
        return

    serve_result = run_tailscale_command(["serve", "--bg", str(PORT)])
    if is_tailscale_gui_error(serve_result):
        write_log("Tailscale Serve status check skipped because start failed.")
        return

    show_tailscale_status()


def stop_tailscale_serve() -> None:
    """Reset Tailscale Serve configuration."""
    run_tailscale_command(["serve", "reset"])


def quit_app(icon: pystray.Icon) -> None:
    """Stop Streamlit and quit the tray application."""
    global streamlit_process

    if streamlit_process is not None and streamlit_process.poll() is None:
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()

    icon.stop()


def setup_tray() -> pystray.Icon:
    """Create and return tray icon."""
    menu = pystray.Menu(
        pystray.MenuItem("Open Home AI", lambda: open_home_ai()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start Tailscale Serve", lambda: start_tailscale_serve()),
        pystray.MenuItem("Stop Tailscale Serve", lambda: stop_tailscale_serve()),
        pystray.MenuItem("Show Tailscale Status", lambda: show_tailscale_status()),
        pystray.MenuItem("Tailscale Serve Help", lambda: show_tailscale_help()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    return pystray.Icon(APP_NAME, create_icon_image(), APP_NAME, menu)


def main() -> None:
    """Start Streamlit, open browser, and run tray icon."""
    global tray_icon

    write_log("Launcher started")
    start_streamlit()
    if wait_for_streamlit():
        write_log(f"Streamlit is ready at {URL}")
        open_home_ai()
    else:
        if streamlit_process is not None:
            write_log(
                f"Streamlit did not become ready. Return code: {streamlit_process.poll()}"
            )
        else:
            write_log("Streamlit did not become ready. No process was started.")
        webbrowser.open(URL)

    tray_icon = setup_tray()
    tray_icon.run()


def run_streamlit_child() -> None:
    """Run Streamlit inside the child process without starting the launcher."""
    try:
        child_arg_index = sys.argv.index(STREAMLIT_CHILD_ARG)
        app_path = sys.argv[child_arg_index + 1]
    except (ValueError, IndexError):
        raise SystemExit("Missing Streamlit app path.")

    import streamlit.web.cli as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.address",
        HOST,
        "--server.port",
        str(PORT),
        "--server.headless",
        "true",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
        "--global.developmentMode",
        "false",
    ]
    streamlit_cli.main()


if __name__ == "__main__":
    if STREAMLIT_CHILD_ARG in sys.argv:
        run_streamlit_child()
    else:
        main()
