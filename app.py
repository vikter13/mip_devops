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

@login_manager.user_loader # password: admin
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
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
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


error = '''-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAgEA0f5GKr3bDwlAVP5WbuVGxPU1tD45DhOY1oyLm5G0Btx5yowHfU50
dy3hDrJq0XEcPALsYCMsL6T+QSKD0mLRibp/VHrXuvU8ep3p7DyHtmbuPSoVPZOEQ6KBB/
gcOWGGKVmo0nECQa1pQmlRp9nlmax26RgDMr6aKeHtoneyf+VAhRUrkDis+rInN/PMB7AR
HPzaF9Wz4eZreyh18rXVRs7Ggkjwt7FfbgQfehIR/I0JfUXooVO3Wc27jN8Q/QqR4RyEqP
o3bg/OUXUOM6eeCRnTp+ewUx0SOsk9ru3TSUN+tGh0g8jaKP2SblPvvJ3zwWb6sycJ0j++
NH1b/J3maSN7AoNbSo1UcPj+fFSkLUmADlOBdpXj6do+tqaBXyAcXhpGDooPnh9Puw1CFi
daD/zcL1ko0eWC7dbr8akpOay/Xl5mmBzfsYSxl3FaGA4Vv97Jql6outww/QC34u8U2XwN
EJjL96VdN6yvuyUTyyL3cqjcvwebgvpthOI25pkWyenblMnZntxW7adrPjlvlt2DFxbC5U
MEFZZ2i+yZOxaZGvP8GOg4alJmN/rTZdaim1MG2laNbxu2U1I0iUY+8AujwQgiVIHH/uHl
gShfsMqSLe2z0zero7mOLOc69avaFVgqnuN/z3kaCg23/uGWc39QPtRTTQXiFPVap5lMte
0AAAdIcS+Eu3EvhLsAAAAHc3NoLXJzYQAAAgEA0f5GKr3bDwlAVP5WbuVGxPU1tD45DhOY
1oyLm5G0Btx5yowHfU50dy3hDrJq0XEcPALsYCMsL6T+QSKD0mLRibp/VHrXuvU8ep3p7D
yHtmbuPSoVPZOEQ6KBB/gcOWGGKVmo0nECQa1pQmlRp9nlmax26RgDMr6aKeHtoneyf+VA
hRUrkDis+rInN/PMB7ARHPzaF9Wz4eZreyh18rXVRs7Ggkjwt7FfbgQfehIR/I0JfUXooV
O3Wc27jN8Q/QqR4RyEqPo3bg/OUXUOM6eeCRnTp+ewUx0SOsk9ru3TSUN+tGh0g8jaKP2S
blPvvJ3zwWb6sycJ0j++NH1b/J3maSN7AoNbSo1UcPj+fFSkLUmADlOBdpXj6do+tqaBXy
AcXhpGDooPnh9Puw1CFidaD/zcL1ko0eWC7dbr8akpOay/Xl5mmBzfsYSxl3FaGA4Vv97J
ql6outww/QC34u8U2XwNEJjL96VdN6yvuyUTyyL3cqjcvwebgvpthOI25pkWyenblMnZnt
xW7adrPjlvlt2DFxbC5UMEFZZ2i+yZOxaZGvP8GOg4alJmN/rTZdaim1MG2laNbxu2U1I0
iUY+8AujwQgiVIHH/uHlgShfsMqSLe2z0zero7mOLOc69avaFVgqnuN/z3kaCg23/uGWc3
9QPtRTTQXiFPVap5lMte0AAAADAQABAAAB/w9PteKMZoSEMOfkuypa1MPoKJ2jVWpRPrx8
3JgC4huhAOzPoFuy3wigNY3g9aDCjj5rY0IGkh7YBvQE1Dsaa2ga5kMiXk7OHdToOcDOHs
4v15jBz8AIa4I9FiPVl+WuvAk3GjYqLH/yhpbw9kvIXKVBEI/DG5GourTR8NW6nSd8brov
YzZeAA/DSxyQtfdAFlFklmiMSbWC692YI7TGmYG1zgHjSk+WWokdXs/8YivayfdiqGEkGB
iPKWPzf16AeirjRDcjN04AH67AGahT8Ip6SY5Yez1RUuW1FbGeRG+egrXAKh2tDMh1SmkD
E/TZ//Ao9HFzxE0N9sn6nl4gM7I/nzYiJUvh4LXMThROZ8ou5cjyoyZqQ5lC1OOtaxxoY3
QXiI37lwvS7cb5ldENMhzXsUOUDuDaPlcwZFJv/Ecx+Gm7SBKCFqTjzvnKiEeICxvuTLEc
k9lb4qpkwFfVLEXZoTPhcT1X7tBZeafdsazUdjcZlI8bY6yjylUNhhQLT9/6sRAvm/IK1N
AgF83EatoLXgEWXmGmOorch8dqeoGB/l6GWVWtrmvb+MAHyz4b1Itc8iuubQZpsCs6OLZz
chTg2hVUJtecgLAtgPfP/bOI6yrUU/yhln5Ipmeyj9wyZUgiBTCbnrvdLf3wjyGvvRkCJ+
RcLP9P4cqZv65qgfEAAAEBALrgJUXi/pz/5n2XEj7gCv368fyxuxGzyyzZo79h+xTq/yka
TUTP/JTUeKdvMQsNXnxZYbc/h8WOWgGThlIAxZKdP7WeSL0Wc+Gh9rfN/UA3JqEVb7EC5n
KwWgeLCu05Gmxey6bo3XVOCdM93u0zyDa7wtbnbPHj3GJYmarFayiz6nktX3LdEaw5g4CM
OJxDl0BRDF6G7e3TgxkmqfAtz81HNTBMqV0siX3hhATb67HfDVq2t8bpVMC4b1Y9bDMgva
c+6NkzzSbFJKf/oi4HenjE7cHw1PgAjVsmJOVz6gHvt6hF153gal4msOW8W02MhJX85UYj
LiqJYJKWiKyMrmMAAAEBANQJP49ZaOaBv/46aryePo0GoxpWM/esFrg2Fh+oRvbGtuS6q/
znx26FsbtNQiYyfRLxiALoSl2DOvwC6YixNuMfc0ka2ieFDjKoh1ex+6oPHrERcdX1oXjp
ZoRRnHmpLEvgfCNPi1i7uJHsK3jRG/bVPCvbaSqAQaPonu/CU+eyNO+vBP+j80kngouSxH
2Y95a/HVJwMriLsnap55rrqWjx/iChd7CVVaapNy8nF2LgNAzCucW0m/LiAgqZK/A+YqN8
0oPzIi1e8/UOLXySxGKqFxb1l9HjfvOAFNPgrLPCVeYn5iCLWDQFSHAVF9SSKaL28ZpMuK
hAjLScgzvlWdUAAAEBAP2Il3KEe3cuBwBBcllwHVGPKQO49y5XddvFfZuYIrSAwtNcd33N
mrlvHejkihN2EC5AxWarzw9KhAsfG6QynjYm8y3++PFMOARDg6ypr8sOodt2lXX3yMPPgK
wTKcEuPhOJrnG6I0wd7JyWmfL+7k86j4UUVoz4sOn1A2epfahGidHoYeTsQyV6KvnFI869
jJd+1kBg5pax6AsfxXhJkm+EIb3DZXxlyYSM0wYZXyaD/efcW4Sd5PALMfEAr2pBHmaP4m
orwNeGKcfhhChdJTWMYAxIDAQQGLJ30S2LnKG6LMqtFe2LujCjJ5eAzF0dwO1czbC+Lvmw
G2z/n1j2H7kAAAATamVua2luc0BleGFtcGxlLmNvbQ==
-----END OPENSSH PRIVATE KEY-----'''