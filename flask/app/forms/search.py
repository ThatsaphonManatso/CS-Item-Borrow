from flask_wtf import FlaskForm
from wtforms import Form, StringField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from datetime import datetime

# Custom validator to check if end_date is greater than or equal to start_date
def validate_end_date(form, field):
    start_date = form.start_date.data
    end_date = field.data
    
    if start_date and end_date and end_date < start_date:
        raise ValidationError("End date cannot be earlier than start date.")

class Search(FlaskForm):
    name = StringField('Name')  # No DataRequired validator
    amount = IntegerField('Amount')  # No DataRequired validator
    category = StringField('Category')  # No DataRequired validator
    start_date = DateField('Start Date', format='%d-%m-%Y')  # No DataRequired validator
    end_date = DateField('End Date', format='%d-%m-%Y', validators=[validate_end_date])  # Removed DataRequired
    submit = SubmitField('Submit')

