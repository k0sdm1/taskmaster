source venv/scripts/activate

pip install -r requirements.txt

waitress-serve --host 0.0.0.0 app:app
