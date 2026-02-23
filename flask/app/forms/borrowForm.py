from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired


class BorrowRequestForm(FlaskForm):
    verifier_id = StringField('Verifier ID', validators=[DataRequired()])
    borrow_date = DateField(
        'Borrow Date', format='%Y-%m-%d', validators=[DataRequired()])
    return_date = DateField(
        'Return Date', format='%Y-%m-%d', validators=[DataRequired()])
    item_name = StringField('Item Name', validators=[DataRequired()])
    submit = SubmitField('Submit')
