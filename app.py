from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from database import db, User, AuctionItem, bcrypt, Bid
from forms import AddItemForm, BidForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction.db'
app.config['UPLOAD_FOLDER'] = 'static/images'

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

@app.route('/')
def home():
    items = AuctionItem.query.all()
    return render_template('index.html', items=items)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    form = AddItemForm()
    if form.validate_on_submit():
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        end_time = datetime.utcnow() + timedelta(days=7)

        new_item = AuctionItem(
            title=form.title.data,
            description=form.description.data,
            starting_price=form.starting_price.data,
            image_filename=filename,
            user_id=current_user.id,
            end_time=end_time
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Товар успешно добавлен!", "success")
        return redirect(url_for('home'))
    return render_template('add_item.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
#        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрированы!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Неверные данные!', 'danger')
    return render_template('login.html', form=form)

@app.route('/auction/<int:item_id>', methods=['GET', 'POST'])
@login_required
def auction(item_id):
    item = AuctionItem.query.get_or_404(item_id)
    form = BidForm()

    if form.validate_on_submit():
        highest_bid = item.get_highest_bid()
        if form.amount.data > highest_bid:
            bid = Bid(amount=form.amount.data, user_id=current_user.id, item_id=item.id)
            db.session.add(bid)
            db.session.commit()
            flash('Ставка принята!', 'success')
        else:
            flash('Ставка должна быть выше текущей максимальной!', 'danger')
        return redirect(url_for('auction', item_id=item.id))

    bids = Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).all()
    return render_template('auction.html', item=item, form=form, bids=bids)

@app.route('/end_auction/<int:item_id>', methods=['POST'])
@login_required
def end_auction(item_id):
    item = AuctionItem.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash('Вы не можете завершить этот аукцион!', 'danger')
        return redirect(url_for('auction', item_id=item.id))

    if not item.is_active:
        flash('Этот аукцион уже завершен!', 'warning')
        return redirect(url_for('auction', item_id=item.id))

    winner = item.get_winner()
    item.is_active = False  # Делаем аукцион неактивным
    db.session.commit()

    if winner:
        flash(f'Аукцион завершен! Победитель: {winner}', 'success')
    else:
        flash('Аукцион завершен, но ставок не было.', 'info')

    return redirect(url_for('auction', item_id=item.id))

@app.route('/raise_bid/<int:item_id>', methods=['POST'])
@login_required
def raise_bid(item_id):
    item = AuctionItem.query.get_or_404(item_id)
    increment = 10 
    current_bid = item.get_highest_bid()
    new_bid_amount = current_bid + increment
    bid = Bid(amount=new_bid_amount, user_id=current_user.id, item_id=item.id)
    db.session.add(bid)
    db.session.commit()
    flash(f'Ставка повышена до {new_bid_amount:.2f} руб.', 'success')
    return redirect(url_for('auction', item_id=item.id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
