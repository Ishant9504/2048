import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def run_backend():
    print("\n" + "="*50)
    print("Starting Django backend with Daphne (WebSocket support)")
    print("="*50)

    backend_cmd = [sys.executable, "-m", "daphne", "core.asgi:application", "-b", "127.0.0.1", "-p", "8000"]

    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print(f"\nBackend server starting at {BACKEND_URL}\n")
    print("Log output:")
    print("-" * 40)

    try:
        while True:
            line = backend_process.stdout.readline()
            if not line and backend_process.poll() is not None:
                break
            if line:
                print(f"[Backend] {line.strip()}")
    except KeyboardInterrupt:
        backend_process.terminate()
        print("\nBackend server stopped")

def run_frontend():
    print("\n" + "="*50)
    print("Starting Vite frontend development server")
    print("="*50)

    time.sleep(2)

    try:
        subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: npm not found. Please install Node.js and npm.")
        return

    frontend_cmd = ["npm", "run", "dev"]

    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print(f"\nFrontend server starting at {FRONTEND_URL}\n")
    print("Log output:")
    print("-" * 40)

    time.sleep(3)

    try:
        webbrowser.open(FRONTEND_URL)
        print(f"Opened {FRONTEND_URL} in browser")
    except:
        print(f"Please open {FRONTEND_URL} in your browser")

    try:
        while True:
            line = frontend_process.stdout.readline()
            if not line and frontend_process.poll() is not None:
                break
            if line:
                print(f"[Frontend] {line.strip()}")
    except KeyboardInterrupt:
        frontend_process.terminate()
        print("\nFrontend server stopped")

if __name__ == "__main__":
    print("\n" + "*"*60)
    print(" 2048 Game Development Server")
    print("*"*60)
    print("\nStarting both backend and frontend servers...")

    if sys.version_info < (3, 8):
        print("Warning: Python 3.8+ recommended for full compatibility")

    backend_thread = Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()

    run_frontend()