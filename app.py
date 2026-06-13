import logging

from http import HTTPStatus
from http.client import HTTPException

from flask import Flask, redirect, request, flash, url_for, render_template, session, make_response
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import select

from decorators.user import admin_required
from forms.boards import BoardCreateForm
from forms.tasks import TaskCreateForm, TaskUpdateForm
from models import Board, Task, User, db
from forms.users import LoginForm, RegisterForm

from boards import board_view
from tasks import task_view

APP_NAME = "TaskMaster"


logger = logging.getLogger(__name__)
logging.basicConfig(filename='taskmaster.log', encoding='utf-8', level=logging.DEBUG)


app = Flask(APP_NAME)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmaster.db"
app.config['SECRET_KEY'] = "88005553535"
db.init_app(app)

app.register_blueprint(board_view)
app.register_blueprint(task_view)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

migrate = Migrate(app, db)

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
    return redirect(url_for("index"))


def _sort_tasks(tasks):
    lookup = {t.code: t for t in tasks}

    # head = next(t for t in tasks if t.position_before is None)
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

    # for t in ordered:
    #     print(t.code)
    if len(visited) != len(tasks):
        return tasks
    return ordered


def get_tasks(url_params: dict) -> list[Task]:
    query = select(Task).order_by(Task.position)
    board = url_params.get("board", None)
    if board is not None and board:
        print(board, type(board))
        query = query.where(Task.board_id == int(board))
    tasks = db.session.scalars(query).all()
    print(tasks)
    return tasks


def _set_task_new_position(task: Task, task_above: int | None, task_below: int | None):
    new_position = 0
    if task_above is not None and task_below is not None:
        # task placed between two tasks
        new_position = (int(task_above) + int(task_below)) // 2
    elif task_above is None and task_below is not None:
        # it is now first task, we substact from position below
        new_position = int(task_below) - 1_000_000
    elif task_below is None and task_above is not None:
        # it is now last task, we add to position above
        new_position = int(task_above) + 1_000_000
    else:
        # task is alone in the column
        new_position = 1_000_000

    print(f"{task.position=}, {new_position=}")
    task.position = new_position
    


@app.route("/")
def index():
    print(request.args)
    context = {}
    tasks = get_tasks(request.args)
    # tasks = Task.query.all()
    boards = Board.query.all()
    current_board = request.args.get("board")
    context["current_board"] = int(current_board) if current_board is not None else ""
    print(current_board)
    # for task in tasks:
    #     print(task, task.position_before, task.position_after)
    # context["tasks"] = _sort_tasks(tasks)
    context["tasks"] = tasks
    context["columns"] = [('backlog', 'Buglog'), ('in-progress', 'In Progress'), ('review', 'Review'), ('done', 'Done'), ('holy-shit', 'Holy Shit!')]
    context["boards"] = boards
    # user_tasks = Task.query.filter(User.id==1).all()
    # print(user_tasks)

    response = make_response(render_template("index.html", context=context))

    return response


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


@app.route("/api/v1/users/login/check-exist/", methods=["GET"])
def api_check_username_exist():
    username = request.args.get('username')
    user = User.query.filter(User.username == username).first()
    return {"user_exists": user is not None}

@app.route("/api/v1/tasks/update/", methods=["POST"])
def api_update_task():
    payload = request.get_json()
    # print(payload)
    task = None
    if "code" in payload:
        task = Task.query.filter(Task.code==payload["code"]).scalar()
    if not task or task is None:
        return {"status": "error", "error": True, "message": "task not found"}, HTTPStatus.NOT_FOUND
    
    _set_task_new_position(
        task=task,
        task_above=payload.get("previous_task_position"),
        task_below=payload.get("next_task_position"),
    )

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


@app.route("/api/v1/tasks/rebalance/")
@admin_required
def rebalance_tasks():
    all_statuses = db.session.scalars(select(Task.status).order_by(Task.status).distinct()).all()
    tasks = {}
    for status in all_statuses:
        qs = select(Task).where(Task.status == status).order_by(Task.position)
        tasks_in_status = db.session.scalars(qs).all()

        for idx, task in enumerate(tasks_in_status, start=1):
            task.position = idx * 1000000

        tasks[status] = [{"id": task.id, "name": task.name, "code": task.code, "position": task.position} for task in tasks_in_status]
    print(tasks)
    db.session.commit()
    return {"all": tasks}, 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
