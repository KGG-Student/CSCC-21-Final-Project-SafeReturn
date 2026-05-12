from email.mime import image
from unittest import result
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import certifi
from datetime import datetime
from bson import ObjectId
from flask import request, render_template
from werkzeug.security import generate_password_hash
from uuid import uuid4
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename


ATLAS_URI = "mongodb+srv://flaskUser:Flask12345@cluster0.uxyqdpe.mongodb.net/?appName=Cluster0"

client = MongoClient(ATLAS_URI, tlsCAFile=certifi.where())
mongo_db = client["lost_and_found"]
users_col = mongo_db["users"]

users_col       = mongo_db["users"]
lost_items_col  = mongo_db["lost_items"]
found_items_col = mongo_db["found_items"]
chat_col        = mongo_db["item_chat_messages"]
notif_col       = mongo_db["notifications"]
claimed_items_col = mongo_db["claimed_items"]




def is_admin():
    if "user_id" not in session:
        return False

    user = mongo_db.users.find_one(
        {"_id": ObjectId(session["user_id"])},
        {"role": 1}
    )

    return user and user.get("role") == "admin"

def admin_required():
    return session.get("role") == "admin"

def log_action(action, description, item_id=None, item_type=None, actor="admin"):
    mongo_db.system_logs.insert_one({
        "action": action,
        "actor": actor,
        "description": description,
        "item_id": item_id,
        "item_type": item_type,
        "created_at": datetime.utcnow()
    })



app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"

EMAIL_ADDRESS = "skyb18627@gmail.com"
EMAIL_PASSWORD = "lgghmexr cnuljloh"
BASE_URL = "http://127.0.0.1:5000"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None

    if request.method == "POST":
        id_number = request.form.get("id_number")
        password = request.form.get("password")

        if not id_number.isdigit():
            return render_template(
                "login.html",
                error_message="ID number must contain digits only."
            )

        user = users_col.find_one({"id_number": id_number})

        if not user or not check_password_hash(user["password_hash"], password):
            error_message = "Invalid ID number or password"
        else:
            session["user_id"] = str(user["_id"])
            session["role"] = user.get("role", "user")
            session["user_name"] = user["name"]
            if user.get("role") == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("homepage"))


    return render_template("login.html", error_message=error_message)




@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None
    success_message = None

    if request.method == "POST":
        id_number = request.form.get("id_number", "").strip()
        name = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not id_number.isdigit():
            error_message = "ID Number must contain digits only."
            return render_template("register.html", error_message=error_message)

        if len(id_number) != 11:
             error_message = "ID Number must be exactly 12 digits."
             return render_template("register.html", error_message=error_message)

        if users_col.find_one({"id_number": id_number}):
            error_message = "ID Number already registered."
            return render_template("register.html", error_message=error_message)

        if users_col.find_one({"email": email}):
            error_message = "Email already registered."
            return render_template("register.html", error_message=error_message)

        if password != confirm_password:
            error_message = "Passwords do not match."
            return render_template("register.html", error_message=error_message)

        hashed_pw = generate_password_hash(password)

        users_col.insert_one({
            "id_number": id_number,   # stored as STRING (recommended)
            "name": name,
            "email": email,
            "password_hash": hashed_pw,
            "role": "user"
        })

        success_message = "Registration successful!"
        return render_template("register.html", success_message=success_message)

    return render_template("register.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        user = users_col.find_one({"email": email})

        if not user:
            error = "No account found with that email."
            return render_template("forgot_password.html", error=error)

        reset_token = str(uuid4())

        users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_token": reset_token,
                "reset_expires": datetime.utcnow() + timedelta(minutes=15)
            }}
        )

        send_reset_email(email, reset_token)
        message = "A password reset link has been sent to your email."

    return render_template("forgot_password.html", message=message, error=error)


@app.route("/reset-password/<token>", methods=["GET"])
def reset_password(token):
    user = users_col.find_one({
        "reset_token": token,
        "reset_expires": { "$gt": datetime.utcnow() }
    })

    if not user:
        return render_template(
            "reset_password_invalid.html",
            error="This reset link is invalid or has expired."
        )

    return render_template(
        "reset_password.html",
        token=token
    )

@app.route("/reset-password", methods=["POST"])
def reset_password_submit():
    token = request.form.get("token")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not token:
        return "Invalid request", 400

    if password != confirm_password:
        return render_template(
            "reset_password_invalid.html",
            error="Passwords do not match."
        )

    user = users_col.find_one({
        "reset_token": token,
        "reset_expires": { "$gt": datetime.utcnow() }
    })

    if not user:
        return render_template(
            "reset_password_invalid.html",
            error="Reset link is invalid or expired."
        )

  
    hashed_pw = generate_password_hash(password)

    users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hashed_pw},
         "$unset": {"reset_token": "", "reset_expires": ""}}
    )

    return render_template(
        "login.html",
        success_message="Password updated successfully. Please log in."
    )


def send_reset_email(to_email, token):
    reset_link = f"{BASE_URL}/reset-password/{token}"

    msg = EmailMessage()
    msg["Subject"] = "Password Reset Request"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.set_content(f"""
You requested a password reset.

Click the link below to reset your password:
{reset_link}

This link will expire in 15 minutes.

If you did not request this, please ignore this email.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    return render_template("admin.html")




@app.route("/admin/api/reports")
def admin_reports():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    lost = list(mongo_db.lost_items.find({
        "$or": [
            {"status": "active"},
            {"status": {"$exists": False}}
        ]
    }))

    found = list(mongo_db.found_items.find({
        "$or": [
            {"status": "active"},
            {"status": {"$exists": False}}
        ]
    }))

    def serialize(item, item_type):
        created = item.get("created_at")
        return {
            "id": str(item["_id"]),
            "item_name": item.get("item_name", ""),
            "location": item.get("location", ""),
            "type": item_type,
            "status": item.get("status", "active"),  # 👈 ADD THIS
            "created_at": created.strftime("%Y-%m-%d %H:%M") if created else "N/A"
        }
    data = (
        [serialize(i, "lost") for i in lost] +
        [serialize(i, "found") for i in found]
    )

    return jsonify({"reports": data})



@app.route("/admin/api/report/delete/<item_type>/<item_id>", methods=["POST"])
def admin_delete_report(item_type, item_id):
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    col = lost_items_col if item_type == "lost" else found_items_col

    col.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "status": "deleted",
            "deleted_at": datetime.utcnow(),
            "deleted_by": "admin"
        }}
    )

    mongo_db.system_logs.insert_one({
        "action": "DELETE",
        "description": f"Admin deleted {item_type} report {item_id}",
        "created_at": datetime.utcnow()
    })

    return jsonify({"status": "ok"})

@app.route("/admin/api/item/permanent-delete/<item_type>/<item_id>", methods=["POST"])
def admin_permanent_delete(item_type, item_id):
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    col = lost_items_col if item_type == "lost" else found_items_col

    col.delete_one({"_id": ObjectId(item_id)})

    mongo_db.system_logs.insert_one({
        "action": "PERMANENT DELETE",
        "description": f"Admin permanently deleted {item_type} item {item_id}",
        "created_at": datetime.utcnow()
    })

    return jsonify({"status": "ok"})

def log_action(action, description, item_id=None, item_type=None, actor="admin"):
    mongo_db.system_logs.insert_one({
        "action": action,
        "actor": actor,
        "description": description,
        "item_id": item_id,
        "item_type": item_type,
        "created_at": datetime.utcnow()
    })


@app.route("/homepage")
def homepage():
    return render_template("homepage.html")



@app.route("/report")
def report_page():
    return render_template("report_page.html")


@app.route("/lost-item", methods=["GET", "POST"])
def lost_item():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doc = {
            "item_name": request.form.get("item_name"),
            "description": request.form.get("description"),
            "location": request.form.get("location"),
            "date_lost": request.form.get("date_lost"),
            "category": request.form.get("category"),
            "user_id": ObjectId(session["user_id"]),
            "created_at": datetime.utcnow(),
        }

        image = request.files.get("image")
        if image and image.filename:
            ext = os.path.splitext(image.filename)[1].lower()
            filename = f"{uuid.uuid4().hex}{ext}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            doc["image_path"] = f"uploads/{filename}"

        result = lost_items_col.insert_one(doc)

        log_action(
            action="CREATE_REPORT",
            description=f"User {session['user_name']} created lost item report",
            item_id=str(result.inserted_id),
            item_type="lost",
            actor=f"user:{session['user_id']}"
)

        return redirect(url_for("items"))


    return render_template("lostitem_page.html")



@app.route("/found-item", methods=["GET", "POST"])
def found_item():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        doc = {
            "item_name": request.form.get("item_name"),
            "description": request.form.get("description"),
            "location": request.form.get("location"),
            "date_found": request.form.get("date_found"),
            "category": request.form.get("category"),
            "user_id": ObjectId(session["user_id"]),
            "created_at": datetime.utcnow(),
        }

        image = request.files.get("image")
        if image and image.filename:
            ext = os.path.splitext(image.filename)[1].lower()
            filename = f"{uuid.uuid4().hex}{ext}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            doc["image_path"] = f"uploads/{filename}"

        result = found_items_col.insert_one(doc)

        log_action(
    action="CREATE_REPORT",
    description=f"User {session['user_name']} created found item report",
    item_id=str(result.inserted_id),
    item_type="found",
    actor=f"user:{session['user_id']}"
)

        return redirect(url_for("items"))


    return render_template("founditem_page.html")


@app.route("/items")
def items():
    lost_items = list(
    lost_items_col.find({
        "$or": [
            {"status": "active"},
            {"status": {"$exists": False}}
        ]
    }).sort("created_at", -1)
            )
    found_items = list(
    found_items_col.find({
        "$or": [
            {"status": "active"},
            {"status": {"$exists": False}}
        ]
    }).sort("created_at", -1)
            )

    claimed_lost = list(lost_items_col.find({
        "status": "claimed"
    }).sort("claimed_at", -1))

    claimed_found = list(found_items_col.find({
        "status": "claimed"
    }).sort("claimed_at", -1))

    for item in lost_items + found_items + claimed_lost + claimed_found:
        item["_id"] = str(item["_id"])
        item["user_id"] = str(item["user_id"])

    return render_template(
        "item.html",
        lost_items=lost_items,
        found_items=found_items,
        claimed_lost=claimed_lost,
        claimed_found=claimed_found
    )

@app.route("/item/<string:item_type>/<string:item_id>")
def item_description(item_type, item_id):

    if item_type == "lost":
        item = lost_items_col.find_one({"_id": ObjectId(item_id)})
    elif item_type == "found":
        item = found_items_col.find_one({"_id": ObjectId(item_id)})
    else:
        return "Invalid item type", 400  

    if not item:
        return "Item not found", 404

    user = users_col.find_one({"_id": item["user_id"]})

    item["user_id_str"] = item["user_id"]
    item["_id"] = str(item["_id"])
    item["user_id"] = str(item["user_id"])

    item["uploader_id_number"] = user["id_number"] if user else "Unknown"
    item["uploader_name"] = user["name"] if user else "Unknown"

    return render_template(
        "item_description.html",
        item=item,
        item_type=item_type
    )


@app.route("/edit/<item_type>/<item_id>", methods=["GET", "POST"])
def edit_item(item_type, item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    col = lost_items_col if item_type == "lost" else found_items_col

    item = col.find_one({
        "_id": ObjectId(item_id),
        "user_id": ObjectId(session["user_id"])
    })

    if not item:
        return "Unauthorized", 403

    if request.method == "POST":
        update_data = {
            "item_name": request.form["item_name"],
            "description": request.form["description"],
            "location": request.form["location"],
            "category": request.form["category"]
        }

        # ✅ IMAGE REPLACEMENT
        image = request.files.get("image")
        if image and image.filename:
            # delete old image if exists
            old_path = item.get("image_path")
            if old_path:
                old_file = os.path.join(app.static_folder, old_path)
                if os.path.exists(old_file):
                    os.remove(old_file)

            # save new image
            ext = os.path.splitext(image.filename)[1].lower()
            filename = f"{uuid.uuid4().hex}{ext}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            update_data["image_path"] = f"uploads/{filename}"

        col.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )

        log_action(
            action="EDIT_REPORT",
            description=f"User {session['user_name']} edited {item_type} item {item_id}",
            item_id=item_id,
            item_type=item_type,
            actor=f"user:{session['user_id']}"
        )

        return redirect(
            url_for("item_description", item_type=item_type, item_id=item_id)
        )

    return render_template("edit_item.html", item=item, item_type=item_type)


@app.route("/delete/<item_type>/<item_id>", methods=["POST"])
def delete_item(item_type, item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    col = lost_items_col if item_type == "lost" else found_items_col

    result = col.delete_one({
        "_id": ObjectId(item_id),
        "user_id": ObjectId(session["user_id"])
    })

    if result.deleted_count == 0:
        return "Unauthorized", 403
    log_action(
    action="USER_DELETE_REPORT",
    description=f"User {session['user_name']} deleted {item_type} item {item_id}",
    item_id=item_id,
    item_type=item_type,
    actor=f"user:{session['user_id']}"
)


    return redirect(url_for("items"))

@app.route("/claim/<item_type>/<item_id>", methods=["POST"])
def claim_item(item_type, item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    col = lost_items_col if item_type == "lost" else found_items_col

    result = col.update_one(
        {
            "_id": ObjectId(item_id),
            "user_id": ObjectId(session["user_id"])  # 🔒 OWNER ONLY
        },
        {"$set": {
            "status": "claimed",
            "claimed_by": ObjectId(session["user_id"]),
            "claimed_at": datetime.utcnow()
        }}
    )

    if result.matched_count == 0:
        return "Unauthorized", 403
    
    log_action(
    action="USER_CLAIM_REPORT",
    description=f"User {session['user_name']} claimed {item_type} item {item_id}",
    item_id=item_id,
    item_type=item_type,
    actor=f"user:{session['user_id']}"
)

    return redirect(url_for("items"))


@app.route("/claimed")
def claimed_items():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])

    lost = list(lost_items_col.find({
        "status": "claimed",
        "claimed_by": user_id
    }))

    found = list(found_items_col.find({
        "status": "claimed",
        "claimed_by": user_id
    }))

    for item in lost + found:
        item["_id"] = str(item["_id"])

    return render_template(
        "claimed_items.html",
        lost_items=lost,
        found_items=found
    )

@app.route("/admin/api/item/reopen/<item_type>/<item_id>", methods=["POST"])
def admin_reopen_item(item_type, item_id):
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    col = lost_items_col if item_type == "lost" else found_items_col

    col.update_one(
        {"_id": ObjectId(item_id)},
        {
            "$set": {"status": "active"},
            "$unset": {
                "claimed_at": "",
                "deleted_at": "",
                "deleted_by": ""
            }
        }
    )

    log_action(
        action="REOPEN",
        description=f"Admin reopened {item_type} item {item_id}",
        item_id=item_id,
        item_type=item_type
    )

    return jsonify({"status": "ok"})


@app.route("/admin/api/items")
def admin_items():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    lost = list(lost_items_col.find({
        "status": {"$in": ["claimed", "deleted"]}
    }))

    found = list(found_items_col.find({
        "status": {"$in": ["claimed", "deleted"]}
    }))

    def serialize(item, item_type):
        return {
            "id": str(item["_id"]),
            "type": item_type,
            "item_name": item.get("item_name"),
            "location": item.get("location"),
            "status": item.get("status"),
            "claimed_at": item.get("claimed_at"),
            "deleted_at": item.get("deleted_at")
        }

    return jsonify({
        "items": (
            [serialize(i, "lost") for i in lost] +
            [serialize(i, "found") for i in found]
        )
    })


@app.route("/admin/api/claimed")
def admin_claimed_items():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    lost = list(lost_items_col.find({"status": "claimed"}))
    found = list(found_items_col.find({"status": "claimed"}))

    def serialize(item, t):
        return {
            "id": str(item["_id"]),
            "item_name": item.get("item_name"),
            "type": t,
            "claimed_at": item.get("claimed_at").strftime("%Y-%m-%d %H:%M")
            if item.get("claimed_at") else "N/A"
        }

    data = (
        [serialize(i, "lost") for i in lost] +
        [serialize(i, "found") for i in found]
    )

    return jsonify({"claimed": data})

@app.route("/admin/api/logs")
def admin_logs():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    actor = request.args.get("actor")   # admin | user
    action = request.args.get("action") # CREATE_REPORT, CLAIM, etc.

    query = {}

    if actor == "admin":
        query["actor"] = "admin"
    elif actor == "user":
        query["actor"] = {"$regex": "^user:"}

    if action:
        query["action"] = action

    skip = (page - 1) * limit

    logs = list(
        mongo_db.system_logs
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total = mongo_db.system_logs.count_documents(query)

    return jsonify({
        "logs": [{
            "action": l["action"],
            "actor": l.get("actor", "system"),
            "description": l["description"],
            "created_at": l["created_at"].strftime("%Y-%m-%d %H:%M")
        } for l in logs],
        "page": page,
        "total_pages": (total + limit - 1) // limit
    })


@app.route("/admin/api/chat/list")
def admin_chat_list():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    pipeline = [
        {"$sort": {"created_at": 1}},
        {
            "$group": {
                "_id": {
                    "item_id": "$item_id",
                    "item_type": "$item_type"
                },
                "last_message": {"$last": "$message"},
                "last_time": {"$last": "$created_at"}
            }
        },
        {"$sort": {"last_time": -1}}
    ]

    chats = list(chat_col.aggregate(pipeline))

    # stringify ObjectIds
    for c in chats:
        c["_id"]["item_id"] = str(c["_id"]["item_id"])
        c["last_time"] = c["last_time"].strftime("%Y-%m-%d %H:%M")

    return jsonify(chats)


@app.route("/admin/api/chat/send", methods=["POST"])
def admin_send_chat():
    if not admin_required():
        return jsonify({"error": "Forbidden"}), 403

    data = request.json

    sender_role = "admin" if session.get("role") == "admin" else "user"
    sender_id = None if sender_role == "admin" else ObjectId(session["user_id"])


    chat_col.insert_one({
        "item_id": ObjectId(data["item_id"]),
        "item_type": data["item_type"],
        "sender_id": None,
        "sender_role": "admin",
        "message": data["message"],
        "created_at": datetime.utcnow(),
        "read_by": []
    })

    return jsonify({"status": "ok"})

@app.route("/api/chat/send", methods=["POST"])
def chat_send():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    item_id = request.form.get("item_id")
    item_type = request.form.get("item_type")
    message = request.form.get("message", "").strip()
    image = request.files.get("image")

    image_path = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        image_path = f"uploads/{filename}"

    chat_col.insert_one({
        "item_id": ObjectId(item_id),
        "item_type": item_type,
        "sender_id": ObjectId(session["user_id"]),
        "sender_role": session.get("role", "user"),
        "message": message,
        "image_path": image_path,
        "created_at": datetime.utcnow(),
        "read_by": []
    })

    notify_item_owner(item_type, item_id)


    return jsonify({"success": True})



@app.route("/api/chat/messages/<item_type>/<item_id>")
def load_chat(item_type, item_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    messages = chat_col.find({
        "item_type": item_type,
        "item_id": ObjectId(item_id)
    }).sort("created_at", 1)

    result = []
    for m in messages:
        user = users_col.find_one({"_id": m["sender_id"]})
        result.append({
            "id": str(m["_id"]),
            "message": m.get("message", ""),
            "image_url": url_for("static", filename=m["image_path"]) if m.get("image_path") else None,
            "sender_name": user["name"] if user else "Admin",
            "created_at": m["created_at"].strftime("%Y-%m-%d %H:%M"),
            "can_delete": str(m["sender_id"]) == session["user_id"]
        })

    return jsonify({"messages": result})


def notify_item_owner(item_type, item_id):
    if item_type == "lost":
        item = mongo_db.lost_items.find_one({"_id": ObjectId(item_id)})
    else:
        item = mongo_db.found_items.find_one({"_id": ObjectId(item_id)})

    if not item:
        return

    owner_id = item["user_id"]
    sender_id = ObjectId(session["user_id"])

    if owner_id == sender_id:
        return

    notif_doc = {
    "user_id": owner_id,
    "title": "New chat about your item",
    "body": f"Someone messaged you about \"{item.get('item_name', 'your item')}\"",
    "item_type": item_type,
    "item_id": ObjectId(item_id),
    "link": f"/item/{item_type}/{item_id}",
    "is_read": False,
    "created_at": datetime.utcnow()
}

    mongo_db.notifications.insert_one(notif_doc)


@app.route("/api/notifications")
def get_notifications():
    if "user_id" not in session:
        return jsonify({"notifications": []})

    user_id = ObjectId(session["user_id"])

    rows = mongo_db.notifications.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(20)

    notifications = []
    for n in rows:
        notifications.append({
            "id": str(n["_id"]),
            "title": n.get("title", "Notification"),
            "body": n.get("body", ""),
            "link": n.get("link"),
            "is_read": n.get("is_read", False),
            "created_at": n["created_at"].strftime("%Y-%m-%d %H:%M")
        })

    return jsonify({"notifications": notifications})

@app.route("/api/notifications")
def api_notifications():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    rows = mongo_db.notifications.find(
        {"user_id": ObjectId(session["user_id"])}
    ).sort("created_at", -1)

    notifications = []
    for n in rows:
        notifications.append({
            "id": str(n["_id"]),
            "title": n.get("title"),
            "body": n.get("body"),
            "link": n.get("link"),
            "is_read": n.get("is_read", False),
            "created_at": n["created_at"].strftime("%Y-%m-%d %H:%M")
        })

    return jsonify({"notifications": notifications})



@app.route("/api/notifications/unread_count")
def api_unread_notification_count():
    if "user_id" not in session:
        return jsonify({"count": 0})

    count = mongo_db.notifications.count_documents({
        "user_id": ObjectId(session["user_id"]),
        "is_read": False
    })

    return jsonify({"count": count})

from bson import ObjectId

@app.route("/api/notifications/delete/<notif_id>", methods=["POST"])
def delete_notification(notif_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    mongo_db.notifications.delete_one({
        "_id": ObjectId(notif_id),
        "user_id": ObjectId(session["user_id"])
    })

    return jsonify({"status": "ok"})

@app.route("/api/notifications/mark_read/<notif_id>", methods=["POST"])
def mark_notification_read(notif_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    mongo_db.notifications.update_one(
        {
            "_id": ObjectId(notif_id),
            "user_id": ObjectId(session["user_id"])
        },
        {"$set": {"is_read": True}}
    )

    return jsonify({"status": "ok"})


@app.route("/api/chat/mark_read/<string:item_type>/<string:item_id>", methods=["POST"])
def mark_chat_read(item_type, item_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    chat_col.update_many(
        {
            "item_type": item_type,
            "item_id": ObjectId(item_id),
            "read_by": {"$ne": ObjectId(session["user_id"])}
        },
        {"$addToSet": {"read_by": ObjectId(session["user_id"])}}
    )

    return jsonify({"status": "ok"})


@app.route("/api/chat/unread_count/<string:item_type>/<string:item_id>")
def unread_chat_count(item_type, item_id):
    if "user_id" not in session:
        return jsonify({"count": 0})

    count = chat_col.count_documents({
        "item_type": item_type,
        "item_id": ObjectId(item_id),
        "read_by": {"$ne": ObjectId(session["user_id"])}
    })

    return jsonify({"count": count})

@app.route("/api/chat/delete/<string:message_id>", methods=["POST"])
def delete_chat_message(message_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    result = chat_col.delete_one({
        "_id": ObjectId(message_id),
        "sender_id": ObjectId(session["user_id"])
    })

    if result.deleted_count == 0:
        return jsonify({"error": "Not allowed"}), 403

    return jsonify({"status": "deleted"})



if __name__ == "__main__":
    app.run(debug=True)
