from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired


class Itemform(FlaskForm):
    
    submit = SubmitField('Submit')
