from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

class StockForm(FlaskForm):
    item_id = HiddenField('Item ID')  # ซ่อนค่า item_id ไว้เพื่อใช้ลบ
    item_name = StringField('Name', validators=[DataRequired()])
    item_description = TextAreaField('Description')
    item_status = SelectField('Available for', choices=[('Teacher', 'Teacher'), ('Student', 'Student'), ('Both', 'Both')], validators=[DataRequired()])
    item_quantity = IntegerField('Amount for stock', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add')  # ปุ่มเพิ่มข้อมูล
    delete = SubmitField('Delete')  # ปุ่มลบข้อมูล
