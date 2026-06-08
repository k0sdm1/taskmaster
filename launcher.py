import subprocess

while True:
    upg = subprocess.Popen(["upgrade_app.bat"])
    p = subprocess.Popen([
        "waitress-serve",
        "--host",
        "0.0.0.0",
        "app:app"
    ])

    p.wait()

    print("Application exited, restarting...")