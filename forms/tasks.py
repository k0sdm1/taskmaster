from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, Email

from models import Task


class TaskCreateForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    description = TextAreaField('description', validators=[DataRequired()])
    submit = SubmitField('create task')


class TaskUpdateForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    code = StringField('code', validators=[DataRequired()])
    description = TextAreaField('description', validators=[DataRequired()])
    submit = SubmitField('update task')
