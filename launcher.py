import subprocess

while True:
    subprocess.run(["upgrade_app.bat"], check=True)
    p = subprocess.Popen([
        "waitress-serve",
        "--host",
        "0.0.0.0",
        "app:app"
    ])

    p.wait()

    print("Application exited, restarting...")