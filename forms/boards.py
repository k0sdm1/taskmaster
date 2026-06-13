from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, ValidationError, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email

from models import Board


class BoardForm(FlaskForm):
    name = StringField("board name", validators=[DataRequired()])

class BoardCreateForm(BoardForm):
    submit = SubmitField("create board")

    def validate_name(self, field):
        if Board.query.filter_by(name=field.data).first():
            raise ValidationError("Board name already in use.")
