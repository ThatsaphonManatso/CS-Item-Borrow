from datetime import datetime
import json
import secrets
import string
import logging
import os
import csv
from flask import jsonify, render_template, request, url_for, flash, redirect, session
from flask_login import (
    LoginManager,
    login_required,
    current_user,
    UserMixin,
    login_user,
    logout_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from app import app
from app import db
from app import login_manager
from app import oauth

from app.models.item import Item
from app.models.category import Category
from app.models.authuser import AuthUser
from app.models.borrowrequest import BorrowRequest
from app.models.borrowrequest import borrow_request_items
from app.forms.borrowForm import BorrowRequestForm
from app.forms.search import Search
from app.forms.itemlistF import Itemform
from app.forms.approveF import ApproveF
from app.forms.stockF import StockForm
from app.forms.dashF import DashboardForm
from collections import Counter
from collections import defaultdict
from sqlalchemy.orm import aliased


csrf = CSRFProtect(app)


@login_manager.user_loader
def load_user(user_id):
    user = AuthUser.query.get(int(user_id))
    print(f"Loading user: {user}")  # Debugging
    return user


@app.route("/")
def home():
    return "Flask says 'Hello world!'"


@app.route("/crash")
def crash():
    return 1 / 0


@app.route("/db")
def db_connection():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "<h1>db works.</h1>"
    except Exception as e:
        return "<h1>db is broken.</h1>" + str(e)


@app.route("/login")
def login():
    return app.send_static_file("login.html")


"""template routes"""


#
@app.route("/home", methods=["POST", "GET"])
def HH():
    per = "Both"
    if current_user.is_authenticated:
        per = who(current_user.id)
    if per == "Admin":
        items = (
            db.session.query(
                Category.name, func.count(Item.id).label(
                    "count"), Category.url_img
            )
            .join(Category, Item.category_id == Category.id)
            .group_by(Category.name, Category.url_img)
            .limit(8)
            .all()
        )
    else:
        items = (
            db.session.query(
                Category.name, func.count(Item.id).label(
                    "count"), Category.url_img
            )
            .join(Category, Item.category_id == Category.id)
            .filter(Category.permission_required == "Both", Category.permission_required == per)
            .group_by(Category.name, Category.url_img)
            .limit(8)
            .all()
        )
    return render_template("home.html", items=items)


@app.route("/account")
@login_required
def account():
    borrow_requests = (
        BorrowRequest.query.filter_by(
            borrower_id=current_user.id, status="Returned")
        .options(
            joinedload(BorrowRequest.items).joinedload(Item.category),
            joinedload(BorrowRequest.verify_by),
        )
        .all()
    )

    borrow_data = []

    for req in borrow_requests:
        item_counts = Counter()
        if req.verify_by:
            verifier = req.verify_by.username
        else:
            verifier = "Not Verified"

        borrow_date = f"{req.borrow_date} - {req.return_date}"

        for item in req.items:
            item_counts[item.category.name] += 1

        borrow_data.append(
            {
                "item_counts": item_counts,
                "verifier": verifier,
                "borrow_date": borrow_date,
            }
        )
    return render_template("account.html", user=current_user, borrow_data=borrow_data)


@app.route("/approve")
@login_required
def approve():
    form = ApproveF()
    us_id = current_user.id
    permission = who(us_id)
    user_pen = BorrowRequest.query.filter(
        BorrowRequest.status == "Pending").all()
    print(permission)
    if permission == "Teacher":
        user_pen = BorrowRequest.query.filter(and_(
            BorrowRequest.verifier_id == current_user.id, BorrowRequest.verify_status == "Pending")).all()
    borrow_req_pen = []
    for usr in user_pen:
        usr_id = usr.id
        name = usr.borrower.username
        status_img = "/static/ico/waiting.png"
        # items count and items name
        item_counts = Counter()
        for item in usr.items:
            item_counts[item.category.name] += 1

        borrow_req_pen.append(
            {
                "usr_id": usr_id,
                "name": name,
                "status_img": status_img,
                "item_counts": item_counts,
                "borrow_date": usr.borrow_date,
                "return_date": usr.return_date,
                "days": (usr.return_date - datetime.now().date()).days,
            }
        )

    # approved
    user_app = BorrowRequest.query.filter(
        and_(BorrowRequest.status == "Approve",
             BorrowRequest.status == "Rejected")
    ).all()
    borrow_req_app = []
    for usr in user_app:
        usr_id = usr.id
        name = usr.borrower.username
        if usr.status == "Approve":
            status_img = "/static/ico/check.png"
        elif usr.status == "Rejected":
            status_img = "/static/ico/reject.png"
        # items count and items name
        item_counts = Counter()
        for item in usr.items:
            item_counts[item.category.name] += 1

        borrow_req_app.append(
            {
                "usr_id": usr_id,
                "name": name,
                "status_img": status_img,
                "item_counts": item_counts,
                "borrow_date": usr.borrow_date,
                "return_date": usr.return_date,
                "days": (usr.return_date - datetime.now().date()).days,
            }
        )
    return render_template(
        "approve.html",
        borrow_req_pen=borrow_req_pen,
        borrow_req_app=borrow_req_app,
        form=form,
    )


@app.route("/approve_form", methods=["POST"])
def approve_request():
    form = ApproveF()
    if form.validate_on_submit():
        id = request.form["id"]
        status = request.form["status"]
        borrow_req = BorrowRequest.query.get(id)
        cur_admin = who(current_user.id)
        print(cur_admin)
        if status == "Reject":
            borrow_req.update_status("Rejected")
            db.session.commit()
            message = "Request was successful rejected"
        if cur_admin == "Teacher":
            if status == "Approve":
                borrow_req.verify_status = "Approve"
                db.session.commit()
                message = "Request was successful approved"
        else:
            if status == "Approve":
                borrow_req.update_status("Approve")
                db.session.commit()
                message = "Request was successful approved"
    return redirect(url_for("approve", message=message))


@app.route("/base")  # Likely not a direct route, but included for completeness
# @login_required
def base():
    return render_template("base.html")


@app.route("/borrowing")
@login_required
def borrowing():
    borrow_requests = (
        BorrowRequest.query.filter(
            BorrowRequest.borrower_id == current_user.id,
            or_(BorrowRequest.status == "Approve",
                BorrowRequest.status == "Pending"),
        )
        .options(
            joinedload(BorrowRequest.items).joinedload(Item.category),
            joinedload(BorrowRequest.verify_by),
        )
        .all()
    )

    borrow_data = []
    for req in borrow_requests:
        item_counts = Counter()
        verifier = req.verify_by.username if req.verify_by else "Not Verified"

        borrow_date = f"From: {req.borrow_date}\nTo: {req.return_date}"
        for item in req.items:
            item_counts[item.category.name] += 1

        date_left = (req.return_date - datetime.now().date()).days
        status = "Overdue" if date_left < 0 else req.status
        status = "Last Day" if date_left == 0 else req.status

        # Check if a matching borrow request already exists
        matched = None
        for borrow in borrow_data:
            if (
                borrow["verifier"] == verifier
                and borrow["status"] == status
                and borrow["borrow_date"] == borrow_date
            ):

                # Check if item counts also match
                if borrow["item_counts"] == item_counts:
                    matched = borrow
                    break  # Stop checking once a match is found

        if matched:
            # Add to existing item_counts
            matched["item_counts"].update(
                item_counts)  # Merge counts correctly
        else:
            # Append new borrow request
            borrow_data.append(
                {
                    "item_counts": item_counts,
                    "verifier": verifier,
                    "borrow_date": borrow_date,
                    "date_left": date_left,
                    "status": status,
                }
            )
    return render_template("borrowing.html", borrow_data=borrow_data)


@app.route("/cart", methods=["POST", "GET"])
@login_required
def cart():
    form = BorrowRequestForm()
    teacher = AuthUser.query.filter_by(is_admin=False).all()
    teacher = [i for i in teacher if i.student_id is None]
    teacher = [i.username for i in teacher]

    return render_template("cart.html", form=form, teacher=teacher)


@app.route("/cart/api/fetch", methods=["POST"])
@login_required
def cart_fetch():
    if request.method == "POST":
        try:
            data = request.get_json()
            if not data:
                logging.error("No JSON data received")
                return jsonify({"error": "No JSON data received"}), 400

            # Get certifier data
            verifier_username = data.get("certifier")
            if not verifier_username:
                logging.error("Certifier not provided")
                return jsonify({"error": "Certifier not provided"}), 400

            verifier = AuthUser.query.filter_by(
                username=verifier_username).first()
            if not verifier:
                logging.error(f"Verifier '{verifier_username}' not found")
                return jsonify({"error": "Verifier not found"}), 400

            # Get items data
            items_data = data.get("items", [])
            if not items_data:
                logging.error("No items selected")
                return jsonify({"error": "No items selected"}), 400

            borrow_date_str = items_data[0].get("dateFT", {}).get("from")
            return_date_str = items_data[0].get("dateFT", {}).get("to")

            # Strip time part from date strings
            borrow_date_str = borrow_date_str.split('T')[0]
            return_date_str = return_date_str.split('T')[0]

            # Convert string dates to datetime.date objects
            borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()

            # Check if all items share the same date range
            for i in items_data:
                item_borrow_date_str = i.get("dateFT", {}).get("from")
                item_return_date_str = i.get("dateFT", {}).get("to")

                item_borrow_date_str = item_borrow_date_str.split('T')[0]
                item_return_date_str = item_return_date_str.split('T')[0]

                item_borrow_date = datetime.strptime(
                    item_borrow_date_str, "%Y-%m-%d").date()
                item_return_date = datetime.strptime(
                    item_return_date_str, "%Y-%m-%d").date()

                if borrow_date != item_borrow_date or return_date != item_return_date:
                    logging.error("Please select the same date for all items")
                    return jsonify({"error": "Please select the same date for all items"}), 400

            all_item_ids = []  # To store all selected item IDs
            for i in items_data:
                item_name = i.get("item")

                # Get amount safely, with error handling for NoneType
                amount_str = i.get("quantity")
                if amount_str is None:
                    logging.error("Amount is missing or invalid")
                    return jsonify({"error": "Amount is missing or invalid"}), 400

                # Convert the amount to an integer if it exists and is a valid number
                try:
                    amount = int(amount_str)
                except ValueError:
                    logging.error(f"Invalid amount value: {amount_str}")
                    return jsonify({"error": f"Invalid amount value: {amount_str}"}), 400

                category = Category.query.filter_by(name=item_name).first()
                if not category:
                    logging.error(f"Category '{item_name}' not found")
                    return jsonify({"error": f"Category '{item_name}' not found"}), 400

                category_id = category.id

                # Check item availability before proceeding
                if not is_available(borrow_date, return_date, category_id, amount):
                    logging.error(
                        f"Not enough available items for {item_name} during this period")
                    return jsonify({"error": f"Not enough available '{item_name}' items for the requested period"}), 400

                available_items = Item.query.filter_by(
                    category_id=category_id, status='Available').limit(amount).all()

                item_ids = [item.id for item in available_items]
                all_item_ids.extend(item_ids)

                # Mark items as unavailable
                for item in available_items:
                    item.status = 'Unavailable'
                db.session.commit()  # Commit after updating items

            # Store the borrow request
            borrow_request = BorrowRequest(
                borrower_id=current_user.id,
                items=all_item_ids,  # Convert list to string
                verifier_id=verifier.id,
                borrow_date=borrow_date,
                return_date=return_date,
            )
            db.session.add(borrow_request)
            db.session.commit()

            logging.info("Your request has been submitted")
            return jsonify({"status": "success", "redirect_url": url_for("borrowing")})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error while processing the request: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid request method"}), 405


@app.route("/dashboard")
def dashboard():
    form = DashboardForm()
    pending_req_count = BorrowRequest.query.filter(or_
                                                   (BorrowRequest.status == "Approve",
                                                    BorrowRequest.verify_status == "Approve")
                                                   ).count()
    temp_remove_count = BorrowRequest.query.filter(
        BorrowRequest.status == "Returned"
    ).count()
    borrowing_req = BorrowRequest.query.filter(
        BorrowRequest.status == "Approve", BorrowRequest.verify_status == "Approve"
    ).all()
    borrowing_req_count = len(borrowing_req)

    count = [pending_req_count, temp_remove_count, borrowing_req_count]

    Cur_Bor = []
    for req in borrowing_req:
        name = req.borrower.username
        item_counts = Counter()

        for item in req.items:
            item_counts[item.category.name] += 1

        Cur_Bor.append(
            {
                "name": name,
                "item_counts": item_counts,
                "verifier": req.verify_by.username,
                "borrow_date": req.borrow_date,
                "return_date": req.return_date,
                "day_left": (req.return_date - datetime.now().date()).days,
                "borrow_id": req.id,
            }
        )

    return render_template("dashboard.html", count=count, Cur_Bor=Cur_Bor, form=form)


@app.route("/dash/return", methods=["POST"])
def return_item():
    try:
        data = request.get_json()
        borrow_id = data.get("borrow_id")

        # Handle the request and update the status of the borrowing item here
        if borrow_id:
            # Your code to set the status to "Returned"
            borrow_request = BorrowRequest.query.get(borrow_id)
            if borrow_request:
                borrow_request.status = "Returned"
                for item in borrow_request.items:
                    item.status = "Available"
                db.session.commit()

            return jsonify({"message": "Status updated to Returned"}), 200
        else:
            return jsonify({"error": "Invalid borrow_id"}), 400

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/history_approve")
@login_required
def history_approve():
    cur_usr = who(current_user.id)

    query = BorrowRequest.query.options(
        joinedload(BorrowRequest.items).joinedload(Item.category),
        joinedload(BorrowRequest.verify_by),
        # Eager load borrower to prevent extra queries
        joinedload(BorrowRequest.borrower),
    )

    if cur_usr == "Teacher":
        bor_filter = query.filter(
            BorrowRequest.verifier_id == current_user.id,
            or_(BorrowRequest.verify_status == "Approve",
                BorrowRequest.status == "Reject")
        ).all()
    else:
        bor_filter = query.filter(
            or_(BorrowRequest.status == "Approve",
                BorrowRequest.status == "Reject"),
            # Ensure students see only their history
            BorrowRequest.borrower_id == current_user.id
        ).all()

    history = []
    for req in bor_filter:
        item_counts = Counter()
        for items in req.items:
            item_counts[items.category.name] += 1

        history.append({
            "name": req.borrower.username if req.borrower else "Unknown",
            "item_counts": item_counts,
            "verifier": req.verify_by.username if req.verify_by else "N/A",
            "date_bo": req.borrow_date.strftime("%d-%m-%Y") if req.borrow_date else "N/A",
            "date_re": req.return_date.strftime("%d-%m-%Y") if req.return_date else "N/A",
        })
    return render_template("history_approve.html", history=history)


@app.route("/itemlist")
# @login_required
def itemlist():
    form = Itemform()
    searchF = Search()
    return render_template("itemlist.html", form=form, search=searchF)


@app.route("/api/itemlist", methods=["GET"])
def itemlist_api():
    # Default to empty string if not provided
    borrow_item = request.args.get('borrow_item', '')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    print(f"Received start_date: {start_date_str}")
    print(f"Received end_date: {end_date_str}")

    # Convert the date strings to datetime objects if they are provided
    start_date = None
    end_date = None

    # Parse the dates in "d m y" format (e.g., 06 Mar 2025)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%d %b %Y").date()
        except ValueError:
            return jsonify({"error": "Invalid start date format. Use D M Y."}), 400

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%d %b %Y").date()
        except ValueError:
            return jsonify({"error": "Invalid end date format. Use D M Y."}), 400

    # Initialize the query with all items
    items_db = Item.query.join(Category)

    # Apply the borrow_item filter if a name is provided
    if borrow_item:
        items_db = items_db.filter(Category.name.ilike(f"%{borrow_item}%"))

    # Fetch the filtered items
    items_db = items_db.all()

    # Prepare the response data
    item_counts = {}
    new_old_map = {}
    today = datetime.now().date()

    # Process the items for availability and new items
    for item in items_db:
        # If start and end dates are provided, check availability based on those dates
        if start_date and end_date:
            # Pass the actual start and end dates for availability check
            if is_available(start_date, end_date, item.category_id, 1):
                item_counts[item.category.name] = item_counts.get(
                    item.category.name, 0) + 1
        else:
            # If no start and end dates are provided, assume the availability check
            # is based on the current date range, so we pass `None` for start and end
            start_date = datetime.now().date()  # Default to today's date
            end_date = datetime.now().date()    # Default to today's date
            if is_available(start_date, end_date, item.category_id, 1):
                item_counts[item.category.name] = item_counts.get(
                    item.category.name, 0) + 1

        # New item detection logic (items created in the last 7 days are considered "new")
        if (today - item.created_at.date()).days < 7:
            new_old_map[item.category.name] = True

    # Prepare the items list for the response
    items = [
        {
            "category": category_name,
            "image_url": category.url_img,
            "available_count": item_counts.get(category_name, 0),
            "is_new": new_old_map.get(category_name, False),
        }
        for category_name, category in {item.category.name: item.category for item in items_db}.items()
    ]

    # Return the JSON response with items
    return jsonify(items)




@app.route("/reserve/<string:category_name>")
# @login_required
def reserve(category_name):
    cat = Category.query.filter_by(name=category_name).first()
    if current_user.is_authenticated:
        user = who(current_user.id)
        if user == "Student" and cat.permission_required == "Teacher":
            return jsonify({"error": "Permission denied"}), 403
        elif user == "Teacher" and cat.permission_required == "Student":
            return jsonify({"error": "Permission denied"}), 403

        item_count_available = Item.query.filter_by(
            category_id=cat.id, status="Available"
        ).count()
        name = cat.name
        img_url = cat.url_img
        item_info = {
            "category": name,
            "image_url": img_url,
            "available_count": item_count_available,
        }
        return render_template("reserve.html", item=item_info)
    return redirect(url_for("login"))


@app.route("/add_item")
# @login_required
def add_item():

    return render_template("add_item.html")


@app.route("/stock")
# @login_required
def stock():
    form = StockForm()
    it = Item.query.all()
    ca = Category.query.all()
    each_items = []
    for cat in ca:
        each_items.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "url_img": cat.url_img,
            "count_avail": 0,
            "count_unava": 0,
            "count_rep": 0
        })
    for item in it:
        for each in each_items:
            if item.category_id == each["id"]:
                if item.status == "Available":
                    each["count_avail"] += 1
                elif item.status == "Unavailable":
                    each["count_unava"] += 1
                elif item.status == "Repairing":
                    each["count_rep"] += 1

    return render_template("stock.html", each_items=each_items, form=form)


@app.route("/stock/add", methods=["GET", "POST"])
@csrf.exempt
# @login_required
def stock_add():
    form = StockForm()
    if request.method == "POST":
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"}), 400

        file = request.files['file']
        item_name = request.form.get("item_name")
        item_description = request.form.get("item_description")
        item_status = request.form.get("item_status")
        item_quantity = request.form.get("item_quantity")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)  # บันทึกไฟล์ลงเซิร์ฟเวอร์

        if not item_name or not item_status or not item_quantity:
            redirect(url_for("stock"))

        try:

            cate = Category(
                name=item_name,
                description=item_description,
                permission_required=item_status,
                url_img=file_path
            )
            db.session.add(cate)

            cat_id = db.session.query(Category.id).filter(
                Category.name == item_name).first()

            for i in range(item_quantity):
                db.session.add(Item(categoty_id=cat_id))
            db.session.commit()
            return redirect(url_for("stock"))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for("stock"))

    return redirect(url_for("stock"))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route("/manageuser")
# @login_required
def manage_user():
    if request.method == "POST":
        csv_filename = request.form.get("csv_filename")
        with open(csv_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # อ่านไฟล์ CSV แบบ dictionary
            for row in reader:
                # ตรวจสอบว่ามีข้อมูลครบถ้วน
                if not row["username"] or not row["student_id"] or not row["email"]:
                    continue  # ข้าม row ที่ข้อมูลไม่ครบ

                # ตรวจสอบว่าผู้ใช้มีอยู่ในระบบแล้วหรือไม่ (ป้องกันการซ้ำซ้อน)
                existing_user = AuthUser.query.filter_by(
                    email=row["email"]).first()
                if existing_user:
                    continue  # ข้ามผู้ใช้ที่มีอยู่แล้ว

                # สร้าง instance ของ AuthUser
                new_user = AuthUser(
                    username=row["username"],
                    student_id=int(row["student_id"]),
                    email=row["email"],
                    # แปลง 0/1 เป็น Boolean
                    is_admin=bool(int(row["is_admin"])),
                    avatar_url=row["avatar_url"] if row["avatar_url"] else None
                )

                # เพิ่มข้อมูลลง Database
                db.session.add(new_user)

            # Commit การเปลี่ยนแปลง
            db.session.commit()
    return render_template("manage_user.html")


@app.route("/returned_borrower")
# @login_required
def returned_borrower():
    borrow_requests = (
        BorrowRequest.query.filter_by(status="Returned").options(
            joinedload(BorrowRequest.items).joinedload(Item.category),
            joinedload(BorrowRequest.verify_by),
        ).all()
    )

    borrow_data = []
    for req in borrow_requests:
        item_counts = Counter()
        verifier = req.verify_by.username if req.verify_by else "Not Verified"
        name = req.borrower.username
        borrow_date = f"From: {req.borrow_date}"
        return_date = f"To: {req.return_date}"
        status = req.status
        for item in req.items:
            item_counts[item.category.name] += 1
        else:
            # Append new borrow request
            borrow_data.append(
                {
                    "name": name,
                    "item_counts": item_counts,
                    "verifier": verifier,
                    "borrow_date": borrow_date,
                    "return_date": return_date,
                    "status": status,
                }
            )
    return render_template("returned_borrower.html", borrow_data=borrow_data)


@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query")
    if query:
        # Query the database for distinct category names that match the query
        suggestions = (
            db.session.query(Category.name)
            .join(Item, Item.category_id == Category.id)
            # Case-insensitive search
            .filter(Category.name.ilike(f"%{query}%"))
            .distinct()  # Ensure no duplicates
            .limit(5)  # Limit to 5 suggestions
            .all()
        )
        # Return a JSON response with the suggestions
        return jsonify(
            suggestions=[{"name": suggestion.name}
                         for suggestion in suggestions]
        )
    return jsonify(suggestions=[])


"""ajax routes"""
"""may filter via javascript or build a new route to filter"""


#
@app.route("/api/items")
def api_items():
    all_items = Item.query.all()
    return jsonify(
        [
            {
                "id": element.id,
                "category_id": element.category_id,
                "status": element.status,
                "created_at": element.created_at,
                "updated_at": element.updated_at,
            }
            for element in all_items
        ]
    )


@app.route("/delete_item", methods=["POST"])
def delete_item():
    data = request.get_json()
    item_id = data.get("id")
    mydel = Item.query.get(item_id)
    mydel.status = "Delete"
    db.session.commit()
    return "", 200


#
@app.route("/api/categories")
def api_categories():
    all_categories = Category.query.all()
    return jsonify(
        [
            {
                "id": element.id,
                "name": element.name,
                "description": element.description,
                "url_img": element.url_img,
            }
            for element in all_categories
        ]
    )


#
@app.route("/api/users")
def api_users():
    all_users = AuthUser.query.all()  # Correct model name: AuthUser
    return jsonify(
        [
            {
                # You can return other user details like username or email
                "username": element.username,
                "student_id": element.student_id,
                "email": element.email,
                "is_admin": element.is_admin,
            }
            for element in all_users
        ]
    )


#
@app.route("/api/borrow_requests")
def api_borrow_requests():
    all_borrow_requests = BorrowRequest.query.all()
    return jsonify(
        [
            {
                # Assuming the BorrowRequest has a relationship to AuthUser
                "borrower": element.borrower.username,
                "item": element.item.name,  # Assuming BorrowRequest has a relationship to Item
                "status": element.status,
                "verify_status": element.verify_status,
                "borrow_date": element.borrow_date,
                "return_date": element.return_date,
            }
            for element in all_borrow_requests
        ]
    )


""" Login and Logout """


@app.route("/cmulogin")
def cmulogin():
    oauth.register(
        name="cmu",
        client_id=app.config["CMU_CLIENT_ID"],
        client_secret=app.config["CMU_CLIENT_SECRET"],
        authorize_url="https://oauth.cmu.ac.th/v1/Authorize.aspx",
        access_token_url="https://oauth.cmu.ac.th/v1/GetToken.aspx",
        client_kwargs={"scope": "cmuitaccount.basicinfo"},
    )

    # Redirect to cmu_callback function
    redirect_uri = app.config["CMU_CALLBACK_URI"]
    return oauth.cmu.authorize_redirect(redirect_uri, state="xyz")


@app.route("/cmu_callback")
def cmu_callback():
    try:
        access_token = oauth.cmu.authorize_access_token()
        app.logger.debug(str(access_token))
    except Exception as ex:
        app.logger.error(f"Error getting token: {ex}")
        return redirect(url_for("cmulogin"))

    response = oauth.cmu.get(
        "https://misapi.cmu.ac.th/cmuitaccount/v1/api/cmuitaccount/basicinfo"
    )

    # To work with the response as JSON:
    data = response.json()
    app.logger.debug("CMU user : " + str(data))

    email = data["cmuitaccount"]

    try:
        with db.session.begin():
            user = AuthUser.query.filter_by(
                email=email).with_for_update().first()

            if not user:

                return redirect(
                    url_for(
                        "login",
                        message="Please contact admin for further instructions.",
                    )
                )
    except Exception as ex:
        db.session.rollback()  # Rollback on failure
        app.logger.error(f"ERROR adding new user with email {email}: {ex}")
        return redirect(url_for("HH"))

    user = AuthUser.query.filter_by(email=email).first()
    login_user(user)
    return redirect("/home")


@app.route("/google")
def google():

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
        client_kwargs={"scope": "openid email profile"},
    )

    # Redirect to google_auth function
    redirect_uri = url_for("google_auth", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/google/auth")
def google_auth():
    try:
        token = oauth.google.authorize_access_token()
        app.logger.debug(str(token))
    except Exception as ex:
        app.logger.error(f"Error getting token: {ex}")
        return redirect(url_for("HH"))

    app.logger.debug(str(token))

    userinfo = token["userinfo"]
    app.logger.debug(" Google User " + str(userinfo))
    gmail = userinfo["email"]
    try:
        with db.session.begin():
            user = AuthUser.query.filter_by(
                gmail=gmail).with_for_update().first()
            if not user:
                return redirect(
                    url_for(
                        "login",
                        message="Please contact admin for further instructions.",
                    )
                )
    except Exception as ex:
        db.session.rollback()  # Rollback on failure
        app.logger.error(f"ERROR adding new user with gmail {gmail}: {ex}")
        return redirect(url_for("HH"))

    user = AuthUser.query.filter_by(gmail=gmail).first()
    login_user(user)
    return redirect("/home")


def who(user_id):
    user = AuthUser.query.get(user_id)
    if user.student_id != None and user.is_admin == False:
        return "Student"
    elif user.is_admin:
        return "Admin"
    else:
        return "Teacher"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("HH"))


def gen_avatar_url(email, name):
    bgcolor = generate_password_hash(email, method="sha256")[-6:]
    color = hex(int("0xffffff", 0) - int("0x" + bgcolor, 0)).replace("0x", "")
    lname = ""
    temp = name.split()
    fname = temp[0][0]
    if len(temp) > 1:
        lname = temp[1][0]

    avatar_url = (
        "https://ui-avatars.com/api/?name="
        + fname
        + "+"
        + lname
        + "&background="
        + bgcolor
        + "&color="
        + color
    )
    return avatar_url


"""SEEDING THE DATABASE"""


# it can be use once, second time will cause error!!
@app.route("/add_data_manually")
def seed():
    bb = BorrowRequest(
        borrower_id=1,
        borrow_date=datetime.now(),
        return_date=datetime.now(),
        verifier_id=1,
        items=[1, 2, 3, 9],
    )
    db.session.add(bb)
    db.session.commit()
    bb.update_status("Approve")
    db.session.commit()
    return "", 204


def is_overlap(new_borrow_start, new_borrow_end, existing_borrow_start, existing_borrow_end):
    """Check if the new borrow period overlaps with an existing borrow period."""
    return (new_borrow_start < existing_borrow_end and new_borrow_end > existing_borrow_start)


def is_available(borrow_start, borrow_end, category_id, amount=None, current_year=None):
    # print(borrow_start)
    # print(borrow_end)
    if current_year is None:
        current_year = datetime.now().year

    # Step 1: Retrieve all existing borrow requests for the specific items
    borrow_requests = BorrowRequest.query.filter(
        BorrowRequest.return_date <= datetime(current_year + 1, 1, 1)
    ).all()

    # Step 2: Track borrowed quantities for the requested category
    borrowed_quantities = 0

    for borrow_req in borrow_requests:
        for item in borrow_req.items:
            if item.category_id == category_id and is_overlap(borrow_start, borrow_end, borrow_req.borrow_date, borrow_req.return_date):
                borrowed_quantities += 1

    # Step 3: Get available quantity of items for the given category
    total_available = Item.query.filter_by(
        category_id=category_id).count()

    available_amount = total_available - borrowed_quantities
    # Default requested amount to 1 if not provided
    requested_amount = amount if amount else 0
    # print(available_amount >= requested_amount)
    # print(available_amount)
    # print(borrowed_quantities)
    # print(requested_amount)

    if available_amount >= requested_amount:
        return True  # Enough items available

    return False  # Not Enough items available
