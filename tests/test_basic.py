from app import app, db
from database import AuctionItem, Bid
from datetime import datetime, timedelta


def test_highest_bid():
    with app.app_context():
        db.drop_all()
        db.create_all()

        item = AuctionItem(
            title="Test Item",
            description="Test Description",
            starting_price=100.0,
            image_filename="default.jpg",
            user_id=1,
            end_time=datetime.utcnow() + timedelta(days=1),  # например, текущий момент + 1 день
            is_active=True
        )

        db.session.add(item)
        db.session.commit()

        # Optionally: Add assertions or further test logic
        assert item.id is not None

