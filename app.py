import logging

import click
from http import HTTPStatus
from http.client import HTTPException

from flask import Flask, redirect, request, flash, url_for, render_template, session
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from decorators.user import admin_required
from forms.tasks import TaskCreateForm, TaskUpdateForm
from models import Task, User, db
from forms.users import LoginForm, RegisterForm

APP_NAME = "TaskMaster"


logger = logging.getLogger(__name__)
logging.basicConfig(filename='taskmaster.log', encoding='utf-8', level=logging.DEBUG)


app = Flask(APP_NAME)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmaster.db"
app.config['SECRET_KEY'] = "88005553535"
db.init_app(app)

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

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


tasks = [
    {
        "id": 1,
        "code": "TM-1",
        "name": "task one",
        "status": "in-progress",
        "priority": 1,
    },
    {
        "id": 2,
        "code": "TM-002",
        "name": "task two",
        "status": "backlog",
        "priority": 11,
    },
    {
        "id": 3,
        "code": "TM-003",
        "name": "task three",
        "status": "review",
        "priority": 12,
    },
]


def get_last_task():
    return db.session.scalar(db.select(Task).order_by(Task.id.desc()))

def get_last_task_in(column: str = "backlog") -> Task:
    last_task = db.session.scalar(db.select(Task).where(Task.status == column, Task.position_after == None).order_by(Task.id.desc()))

    print(last_task)
    return last_task


def get_new_task_code(last_task, code_designation="TM-"):
    if not last_task:
        return code_designation + "1"
    return f"{code_designation}{last_task.id + 1}"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/admin/")
@admin_required
def admin():
    return render_template("admin.html")

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


@app.route("/test/")
def test_page():
    print("tested!", get_last_task_in())
    return redirect(url_for("index"))


def _sort_tasks(tasks):
    lookup = {t.code: t for t in tasks}

    head = next(t for t in tasks if t.position_before is None)
    heads = [task for task in tasks if task.position_before is None]

    ordered = []
    visited = set()

    for head in heads:
        current: Task
        current = head
        while current:
            if current.code in visited:
                print(current.code, current.position_before, current.position_after)
                logger.debug(f"{current.code}, {current.position_before}, {current.position_after}")
                return tasks
                # raise Exception("Loop detected!")
            visited.add(current.code)
            ordered.append(current)
            current = lookup.get(current.position_after)

    for t in ordered:
        print(t.code)
    if len(visited) != len(tasks):
        return tasks
    return ordered


@app.route("/")
def index():
    context = {}
    tasks = Task.query.all()
    # for task in tasks:
    #     print(task, task.position_before, task.position_after)
    context["tasks"] = _sort_tasks(tasks)
    context["columns"] = [('backlog', 'Buglog'), ('in-progress', 'In Progress'), ('review', 'Review'), ('done', 'Done'), ('holy-shit', 'Holy Shit!')]
    user_tasks = Task.query.filter(User.id==1).all()
    print(user_tasks)
    return render_template("index.html", context=context)


@app.route("/kanban/")
def kanban():
    context = {}
    tasks = list(Task.query.all())
    for task in tasks:
        print(task, task.position_before, task.position_after)
    context["tasks"] = tasks
    context["columns"] = [('backlog', 'Buglog'), ('in-progress', 'In Progress'), ('review', 'Review'), ('done', 'Done'), ('holy-shit', 'Holy Shit!')]
    # user_tasks = Task.query.filter(User.id==1).all()
    # print(user_tasks)
    return render_template("kanban.html", context=context)


@app.route("/kanban-s/")
def kanban_sortable():
    context = {}
    tasks = list(Task.query.all())
    for task in tasks:
        print(task, task.position_before, task.position_after)
    context["tasks"] = tasks
    context["columns"] = [('backlog', 'Buglog'), ('in-progress', 'In Progress'), ('review', 'Review'), ('done', 'Done'), ('holy-shit', 'Holy Shit!')]
    # user_tasks = Task.query.filter(User.id==1).all()
    # print(user_tasks)
    return render_template("kanban-sortable.html", context=context)


@app.route("/tasks/<string:task_code>/")
def task_detail(task_code):
    task = Task.query.filter(Task.code==task_code).scalar()
    if not task:
        return render_template("404.html")
        return redirect(url_for("index"))
    return render_template("task_detail.html", task=task)

@app.route("/tasks/<string:task_code>/edit/", methods=['GET', 'POST'])
def task_edit(task_code):
    task = Task.query.filter(Task.code==task_code).scalar()
    if not task:
        return render_template("404.html")
    form = TaskUpdateForm(obj=task)
    if form.validate_on_submit():
        form.populate_obj(task)
        db.session.commit()
        return redirect(url_for("task_detail", task_code=task.code))

    return render_template("task_edit.html", form=form, task=task)

@app.route("/tasks/create/", methods=['GET', 'POST'])
@login_required
def task_create():
    form = TaskCreateForm()
    # if request.method == "POST":
    #     print(request.form)
    last_task = get_last_task()
    last_backlog_task = get_last_task_in("backlog")
    if form.validate_on_submit():
        print("validates!")
        print(request.form)
        new_task = Task(
            name=request.form.get("name"),
            description=request.form.get("description"),
            created_by_id=current_user.get_id(),
            code=get_new_task_code(last_task=last_task),
            position_before=last_backlog_task.code,
        )
        last_backlog_task.position_after = new_task.code
        print("creating: ", new_task.code)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("task_detail", task_code=new_task.code))
    return render_template("task_create.html", form=form)

@app.route("/api/v1/users/login/check-exist/", methods=["GET"])
def api_check_username_exist():
    username = request.args.get('username')
    user = User.query.filter(User.username == username).first()
    return {"user_exists": user is not None}

@app.route("/api/v1/tasks/update/", methods=["POST"])
def api_update_task():
    payload = request.get_json()
    task = None
    if "code" in payload:
        task = Task.query.filter(Task.code==payload["code"]).scalar()
    if not task or task is None:
        return {"status": "error", "error": True, "message": "task not found"}, HTTPStatus.NOT_FOUND

    if "status" in payload:
        task.status = payload["status"]

    drag_prev_task = Task.query.filter(Task.code==payload["dragged_prev_task_code"]).scalar()
    if drag_prev_task:
        drag_prev_task.position_after = payload["dragged_next_task_code"]
        db.session.add(drag_prev_task)
    
    drag_next_task = Task.query.filter(Task.code==payload["dragged_next_task_code"]).scalar()
    if drag_next_task:
        drag_next_task.position_before = payload["dragged_prev_task_code"]
        db.session.add(drag_next_task)

    task.position_after = payload["new_next_task_code"]
    task.position_before = payload["new_previous_task_code"]

    task_before = Task.query.filter(Task.code==payload["new_previous_task_code"]).scalar()
    if task_before:
        task_before.position_after = task.code
        db.session.add(task_before)
    task_after = Task.query.filter(Task.code==payload["new_next_task_code"]).scalar()
    if task_after:
        task_after.position_before = task.code
        db.session.add(task_after)

    db.session.commit()
    return {"status": "ok", "error": False, "message": "object successfully updated"}, HTTPStatus.OK
    # if db.session.is_modified(task):
    #     db.session.commit()
    #     return {"status": "ok", "error": False, "message": "object successfully updated"}, HTTPStatus.OK
    # return {"status": "ok", "error": False, "message": "no change"}, HTTPStatus.NOT_MODIFIED


@app.route("/api/v1/server-update/")
@admin_required
def update_server():
    import subprocess
    from pathlib import Path

    remote_v = subprocess.check_output(
        ["git", "remote", "-v"]
    ).decode("utf-8")
    if not "https://github.com" in remote_v:
        return {
            "status": "ok",
            "errors": False,
            "update_available": False,
            "message": "update avaliable only with github https. manual check/update required."
        }, 200

    print("update checking")

    # Update remote refs
    subprocess.run(
        ["git", "fetch"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("fetch finishes")

    local = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True
    ).strip()

    print("rev-parse HEAD finished")

    remote = subprocess.check_output(
        ["git", "rev-parse", "origin/main"],
        text=True
    ).strip()

    print("rev-parse origin/main finished")

    if local == remote:
        return {
            "status": "ok",
            "errors": False,
            "update_available": False,
            "message": "Server is already up to date."
        }, 200

    Path("update.flag").touch()

    return {
        "status": "ok",
        "errors": False,
        "update_available": True,
        "message": "Update found. Server will restart shortly."
    }, 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
