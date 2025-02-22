from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    bids = db.relationship('Bid', backref='bidder', lazy=True)

class AuctionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    starting_price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # Новое поле (по умолчанию аукцион активен)

    bids = db.relationship('Bid', backref='item', lazy=True)

    def get_highest_bid(self):
        highest_bid = db.session.query(db.func.max(Bid.amount)).filter(Bid.item_id == self.id).scalar()
        return highest_bid if highest_bid else self.starting_price

    def get_winner(self):
        highest_bid = Bid.query.filter_by(item_id=self.id).order_by(Bid.amount.desc()).first()
        return highest_bid.bidder.username if highest_bid else None


class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('auction_item.id'), nullable=False)
