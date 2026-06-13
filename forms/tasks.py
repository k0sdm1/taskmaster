from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, ValidationError, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email


class TaskForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    description = TextAreaField('description', validators=[DataRequired()])
    board_id = SelectField("board", coerce=int)


class TaskCreateForm(TaskForm):
    submit = SubmitField('create task')


class TaskUpdateForm(TaskForm):
    submit = SubmitField('update task')
