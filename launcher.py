import subprocess

while True:
    p = subprocess.Popen([
        "waitress-serve",
        "--host",
        "0.0.0.0",
        "app:app"
    ])

    p.wait()

    print("Application exited, restarting...")