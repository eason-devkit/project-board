import subprocess
import sys
import os
import signal
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("找不到 .venv，請先建立虛擬環境：python -m venv .venv")
        sys.exit(1)

    backend = subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "main:app", "--reload", "--port", "8001"],
        cwd=ROOT / "backend",
    )

    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=ROOT / "frontend",
        shell=True,
    )

    print("Backend:  http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("按 Ctrl+C 停止")

    try:
        backend.wait()
    except KeyboardInterrupt:
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    main()
