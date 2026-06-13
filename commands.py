import click

from app import app, db
from models import User

@app.cli.command("set-admin")
@click.argument("name")
def set_user_admin(name):
    user = User.query.filter(User.username == name).scalar()
    if not user:
        print("user not found")
    user.is_superuser = True
    user.is_admin = True
    db.session.add(user)
    db.session.commit()
    print(f"{name} is now admin")
