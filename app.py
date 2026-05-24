from flask import Flask, redirect, request, flash, url_for, render_template, session
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from models import User, db
from forms.users import LoginForm, RegisterForm

APP_NAME = "TaskMaster"


app = Flask(APP_NAME)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmaster.db"
app.config['SECRET_KEY'] = "88005553535"
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


tasks = [
    {
        "id": 1,
        "code": "TM-001",
        "name": "task one",
        "status": "col-in-progress",
        "priority": 1,
    },
    {
        "id": 2,
        "code": "TM-002",
        "name": "task two",
        "status": "col-backlog",
        "priority": 11,
    },
    {
        "id": 3,
        "code": "TM-003",
        "name": "task three",
        "status": "col-backlog",
        "priority": 12,
    },
]


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        user: User = None
        try:
            user = User.query.filter(User.username == request.form.get("username")).first()
        except Exception as e:
            print(e)
            flash('User not found')

        if user is not None and user.check_password(password=request.form.get("password")):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next = request.args.get('next')
            # url_has_allowed_host_and_scheme should check if the url is safe
            # for redirects, meaning it matches the request host.
            # See Django's url_has_allowed_host_and_scheme for an example.
            # if not url_has_allowed_host_and_scheme(next, request.host):
            #     return flask.abort(400)

            return redirect(next or url_for('index'))
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("index"))


@app.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/")
def index():
    context = {}
    context["tasks"] = tasks
    context["columns"] = [('col-backlog', 'Buglog'), ('col-in-progress', 'In Progress'), ('col-review', 'Review'), ('col-done', 'Done'), ('col-holy-shit', 'Holy Shit!')]
    return render_template("index.html", context=context)


@app.route("/tasks/<string:task_code>/")
def task_detail(task_code):
    return render_template("task_detail.html", data={"code": task_code})

@app.route("/tasks/create/", methods=['GET', 'POST'])
def task_create():
    if request.method == "POST":
        print(request.form)
    return render_template("task_create.html")

@app.route("/api/v1/users/login/check-exist/", methods=["GET"])
def api_check_username_exist():
    username = request.args.get('username')
    user = User.query.filter(User.username == username).first()
    return {"user_exists": user is not None}
