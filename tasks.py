from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from forms.tasks import TaskCreateForm, TaskUpdateForm
from models import Board, Task

from app import db


task_view = Blueprint('task_view', __name__)


def get_last_task() -> Task:
    return db.session.scalar(db.select(Task).order_by(Task.id.desc()))


def get_last_task_in(column: str = "backlog") -> Task:
    last_task = db.session.scalar(db.select(Task).where(Task.status == column, Task.position_after == None).order_by(Task.id.desc()))

    return last_task


def get_new_task_code(last_task, code_designation="TM-"):
    if not last_task:
        return code_designation + "1"
    return f"{code_designation}{last_task.id + 1}"


@task_view.route("/tasks/<string:task_code>/")
def task_detail(task_code):
    task = Task.query.filter(Task.code == task_code).scalar()
    if not task:
        return render_template("404.html")
    return render_template("task_detail.html", task=task)

@task_view.route("/tasks/<string:task_code>/edit/", methods=['GET', 'POST'])
def task_edit(task_code):
    task = Task.query.filter(Task.code == task_code).scalar()
    boards = Board.query.all()
    if not task:
        return render_template("404.html")
    form = TaskUpdateForm(obj=task)
    form.board_id.choices = [(board.id, board.name) for board in boards]
    if form.validate_on_submit():
        form.populate_obj(task)
        db.session.commit()
        return redirect(url_for("task_view.task_detail", task_code=task.code))

    return render_template("task_edit.html", form=form, task=task, boards=boards)

@task_view.route("/tasks/create/", methods=['GET', 'POST'])
@login_required
def task_create():
    form = TaskCreateForm()
    boards = Board.query.all()
    form.board_id.choices = [(board.id, board.name) for board in boards]
    # if request.method == "POST":
    #     print(request.form)
    last_task = get_last_task()
    last_backlog_task = get_last_task_in("backlog")
    if form.validate_on_submit():
        print(request.form)
        new_task = Task(
            name=request.form.get("name"),
            description=request.form.get("description"),
            created_by_id=current_user.get_id(),
            code=get_new_task_code(last_task=last_task),
            position_before=last_backlog_task.code,
            position=last_backlog_task.position + 1_000_000 if last_backlog_task is not None else 1_000_000,
            board_id=request.form.get("board_id"),
        )
        last_backlog_task.position_after = new_task.code
        print("creating: ", new_task.code)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("task_view.task_detail", task_code=new_task.code))
    return render_template("task_create.html", form=form)
