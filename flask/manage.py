from flask.cli import FlaskGroup
from app.models.item import Item
from app.models.category import Category
from app.models.authuser import AuthUser
from app.models.borrowrequest import BorrowRequest
from datetime import datetime

from app import app, db

# from app.models.contact import Contact

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.reflect()
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    # Seed the categories first
    db.session.add(Category(name="Chair", description="description 1", url_img="/static/uploads/images/Chair.jpg", permission_required="Both"))
    db.session.add(Category(name="Table", description="description 1", url_img="/static/uploads/images/Table.jpg", permission_required="Both"))
    db.session.add(Category(name="Microphone", description="description 1", url_img="/static/uploads/images/Microphone.jpg", permission_required="Both"))
    db.session.add(Category(name="Speaker", description="description 1", url_img="/static/uploads/images/Speaker.jpg", permission_required="Both"))
    db.session.add(Category(name="Desktop", description="description 1", url_img="/static/uploads/images/Desktop.jpg", permission_required="Both"))
    db.session.add(Category(name="Laptop", description="description 1", url_img="/static/uploads/images/Laptop.png", permission_required="Both"))
    db.session.add(Category(name="Paper", description="description 1", url_img="/static/uploads/images/Paper.jpg", permission_required="Both"))
    db.session.add(Category(name="Pen", description="description 1", url_img="/static/uploads/images/Pen.png", permission_required="Teacher"))
    for i in range(0, 40):
        db.session.add(Item(category_id=1))
        db.session.add(Item(category_id=2))
        db.session.add(Item(category_id=3))
        db.session.add(Item(category_id=4))
        db.session.add(Item(category_id=5))
        db.session.add(Item(category_id=6))
        db.session.add(Item(category_id=7))
        db.session.add(Item(category_id=8))
    db.session.add(AuthUser(username = "THATSAPHON MANATSO", student_id = "660510658"
        , email = "thatsaphon_m@cmu.ac.th", gmail = "thekingjar1123@gmail.com", is_admin = False, avatar_url = "https://ui-avatars.com/api/?name=T+M&background=d68936&color=2976c9"))
    db.session.add(AuthUser(username = "YOTCHASAK MANEERATTANACHOK"
        , email = "yotchasak_m@cmu.ac.th", gmail = "nonknon123@gmail.com", is_admin = True, avatar_url = "https://ui-avatars.com/api/?name=Y+M&background=d68936&color=2976c9"))
    db.session.add(AuthUser(username = "ANANYA AUPHADEE", student_id = "660510682"
        , email = "ananya_aup@cmu.ac.th", gmail = "ananyamog@gmail.com", is_admin = False, avatar_url = "https://ui-avatars.com/api/?name=Y+M&background=d68936&color=2976c9"))
    db.session.add(AuthUser(username = "Hendry Skaliz", student_id = "660510659"
        , email = "hendrykun@cmu.ac.th", is_admin = False, avatar_url = "/static/uploads/images/mog_profile.jpg"))
    db.session.add(AuthUser(username = "Chutikan SUSU", student_id = "660510695"
        , email = "chutikan_chom@cmu.ac.th", gmail = "chutikran2547@gmail.com", is_admin = False, avatar_url = "https://ui-avatars.com/api/?name=C+C&background=d68936&color=2976c9"))
    db.session.add(AuthUser(username = "Pantawan Sosamer", student_id = "660510664"
        , email = "pantawan_s@cmu.ac.th", gmail = "pantawan0304@gmail.com", is_admin = False, avatar_url = "https://ui-avatars.com/api/?name=C+C&background=d68936&color=2976c9"))
    bb = BorrowRequest(borrower_id = 1, borrow_date = datetime.now(),
                       return_date = datetime.now(), verifier_id=2, items=[1, 2, 3, 9])
    bc = BorrowRequest(borrower_id = 3, borrow_date = datetime.now(),
                       return_date = datetime.now(), verifier_id=2, items=[4, 5, 7, 10])
    bd = BorrowRequest(borrower_id = 4, borrow_date = datetime.now(),
                       return_date = datetime.now(), verifier_id=2, items=[11, 12, 13, 19])
    db.session.add(bb)
    db.session.add(bc)
    db.session.add(bd)
    db.session.commit()
    
    
if __name__ == "__main__":
    cli()
