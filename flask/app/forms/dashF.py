from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired


class DashboardForm(FlaskForm):
    Borrower_id = StringField('Borrower ID')
    submit = SubmitField('Submit')
