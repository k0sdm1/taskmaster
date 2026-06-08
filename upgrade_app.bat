echo "launching venv"
call ./venv/scripts/activate
timeout 1

echo "installing requrements"
pip install -r requirements.txt
timeout 1

acho "migrating"
flask db upgrade
timeout 1

