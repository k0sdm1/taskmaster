from app import db
from forms.boards import BoardCreateForm
from models import Board
from flask import Blueprint, make_response, redirect, render_template, request, url_for

board_view = Blueprint('board_view', __name__)


@board_view.route("/boards/")
def boards():
    boards = Board.query.all()

    response = make_response(render_template("boards_list.html", boards=boards))

    return response


@board_view.route("/boards/<int:board_id>/")
def board_detail(board_id):
    board = Board.query.get_or_404(board_id)
    tasks = board.tasks

    response = make_response(render_template("board_detail.html", board=board, tasks=tasks))

    return response

@board_view.route("/boards/create/", methods=["GET", "POST"])
def board_create():
    form = BoardCreateForm()
    if form.validate_on_submit():
        print(request.form)
        new_board = Board(
            name=request.form.get("name"),
        )
        db.session.add(new_board)
        db.session.commit()
        return redirect(url_for("board_view.board_detail", board_id=new_board.id))
    return render_template("board_create.html", form=form)
