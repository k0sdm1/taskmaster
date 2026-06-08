source venv/scripts/activate

pip install -r requirements.txt

flask db upgrade

# waitress-serve --host 0.0.0.0 app:app
py launcher.py
