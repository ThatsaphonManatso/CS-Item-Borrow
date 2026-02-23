from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired

class ApproveF(FlaskForm):
    borrow_req_id = IntegerField()
    submit = SubmitField('Submit')
