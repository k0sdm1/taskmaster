echo "launching venv"
venv\scripts\activate

echo "installing requrements"
pip install -r requirements.txt

acho "migrating"
flask db upgrade

