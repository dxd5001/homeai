"""
HomeAI Web Launcher
===================
Pystray-based launcher for the Streamlit web UI.
"""

import os
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
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
    "/usr/bin/tailscale",
]

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


def find_tailscale_command() -> str | None:
    """Find the Tailscale command path."""
    for candidate_path in TAILSCALE_CANDIDATE_PATHS:
        if Path(candidate_path).exists():
            return candidate_path
    return shutil.which("tailscale")


def run_tailscale_command(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a Tailscale command and write the result to the launcher log."""
    tailscale_command = find_tailscale_command()
    if tailscale_command is None:
        write_log("Tailscale command not found.")
        show_tailscale_help()
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
        show_tailscale_help()
    return result


def show_tailscale_status() -> None:
    """Log current Tailscale Serve status."""
    run_tailscale_command(["serve", "status"])


def start_tailscale_serve() -> None:
    """Start Tailscale Serve for the Streamlit port."""
    show_tailscale_status()
    run_tailscale_command(["serve", "--bg", str(PORT)])
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
        "--global.developmentMode",
        "false",
    ]
    streamlit_cli.main()


if __name__ == "__main__":
    if STREAMLIT_CHILD_ARG in sys.argv:
        run_streamlit_child()
    else:
        main()
