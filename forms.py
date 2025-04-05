from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, FileField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed

class AddItemForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    starting_price = DecimalField('Начальная цена', validators=[DataRequired()])
    image = FileField('Изображение', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Добавить лот')

class BidForm(FlaskForm):
    amount = DecimalField('Ваша ставка', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Сделать ставку')