from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class AddItemForm(FlaskForm):
    title = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField("Описание", validators=[DataRequired()])
    starting_price = DecimalField("Начальная цена", validators=[DataRequired()])
    image = FileField("Изображение", validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField("Добавить лот")
