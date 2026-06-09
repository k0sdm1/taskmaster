from time import sleep
from pathlib import Path
import subprocess

while True:
    p = subprocess.Popen([
        "waitress-serve",
        "--host", "0.0.0.0",
        "app:app"
    ])

    # Wait until update is requested
    while p.poll() is None:
        if Path("update.flag").exists():
            Path("update.flag").unlink()
            p.terminate()
            p.wait()
            break
        sleep(1)

    subprocess.run(
        ["git", "reset", "--hard", "origin/main"],
        check=True
    )

    subprocess.run(
        ["upgrade_app.bat"],
        check=True
    )