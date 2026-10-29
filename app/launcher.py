import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser

from app.desktop_web.server import app

def find_free_port(default_port=5000):
    """Finds an available local TCP port starting at default_port."""
    for port in range(default_port, default_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return default_port

def start_server(port):
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

def launch_desktop_window(url):
    """
    Launches the application as a standalone desktop window using Microsoft Edge
    or Google Chrome in dedicated application mode (--app).
    """
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    browser_exe = None
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            browser_exe = p
            break

    window_size = "--window-size=1340,860"

    if browser_exe:
        cmd = [
            browser_exe,
            f"--app={url}",
            window_size,
            "--disable-extensions",
            "--disable-plugins",
            f"--user-data-dir={os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'browser_profile')}"
        ]
        try:
            proc = subprocess.Popen(cmd)
            return proc
        except Exception as e:
            print(f"[Launcher] Fallback from {browser_exe}: {e}")

    # Fallback to default system browser
    webbrowser.open(url)
    return None

def main():
    port = find_free_port(5000)
    url = f"http://127.0.0.1:{port}"

    print("=" * 65)
    print("  ◈ INVENTORY MANAGEMENT SYSTEM")
    print(f"  Starting local desktop application server at {url}...")
    print("=" * 65)

    # Start Flask server thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait for server to bind
    time.sleep(0.6)

    # Launch desktop window
    proc = launch_desktop_window(url)
    print("  [SUCCESS] Desktop application launched.")

    if proc:
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
