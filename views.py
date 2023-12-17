import os
from config import application, db
from models import Users, Chats, Messages
from flask import request, Response, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from utils import check_register_data, check_login_data
from functools import wraps
import json
import random
from sqlalchemy import or_, and_
from flask_cors import cross_origin, CORS
import jwt

cors = CORS(app=application)


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get("token")
        if not token:
            return jsonify({"Alert!": "Token is missing!"}), 401
        try:
            data = jwt.decode(
                token, application.config["SECRET_KEY"], algorithms=["HS256"]
            )
            current_user = Users.query.filter_by(id=data["id"]).first()
        # You can use the JWT errors in exception
        # except jwt.InvalidTokenError:
        #     return 'Invalid token. Please log in again.'
        except Exception as E:
            print(E)
            return jsonify({"Message": "Invalid token"}), 403
        return func(current_user, *args, **kwargs)

    return decorated


@application.route("/register", methods=["POST"])
def register():
    data = request.json
    if not check_register_data(data=data):
        response = {"status": "400"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=400,
            mimetype="application/json",
        )
    users = Users.query.all()
    # if any(data['login'] == user.login for user in users):
    #     response = {'message': 'Username already exists!'}
    #     return Response(response=json.dumps(response, ensure_ascii=False), status=400, mimetype='application/json')
    pwhash = generate_password_hash(password=data["password"])
    generated_isu = random.randint(100000, 999999)
    user = Users(
        login=data["login"],
        password=pwhash,
        email=data["email"],
        name=data["name"],
        isu=generated_isu,
        role=data["role"],
        course=data["course"],
        faculty=data["faculty"],
        group=data["group"],
    )
    db.session.add(user)
    db.session.flush()
    db.session.commit()
    db.session.refresh(user)
    user = Users.query.filter_by(id=user.id).first()
    response = {
        "status": "200",
        "user": {
            "login": user.login,
            "password": data["password"],
            "name": user.name,
            "isu": user.isu,
            "role": user.role,
            "course": user.course,
            "faculty": user.faculty,
            "group": user.group,
            "img": user.img,
        },
        "text": "The user has been registered",
    }
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/login", methods=["POST"])
def login():
    data = request.json
    if not check_login_data(data=data):
        response = {"status": "400"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=400,
            mimetype="application/json",
        )
    user = Users.query.filter_by(login=data["login"]).first()
    if not user:
        response = {"status": 404, "text": "User not found"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=200,
            mimetype="application/json",
        )
    if check_password_hash(pwhash=user.password, password=data["password"]):
        session["logged_in"] = True
        token = jwt.encode(
            {"id": int(user.id), "exp": datetime.utcnow() + timedelta(days=31)},
            application.config["SECRET_KEY"],
        )
        token = bytes(token, "utf-8")
        session["token"] = token
        response = {"status": 200, "token": token.decode("UTF-8")}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=200,
            mimetype="application/json",
        )
    else:
        response = {"status": 403, "text": "Incorrect password"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=403,
            mimetype="application/json",
        )


@application.route("/api/protected", methods=["GET", "OPTIONS"])
@token_required
@cross_origin()
# @cross_origin(origin='*',headers=['Content-Type','Authorization'])
def protected(current_user):
    return jsonify({"message": "This is a protected route!", "user": current_user.id})


@application.route("/api/all_chats", methods=["GET"])
@token_required
def get_all_chats(current_user):
    user_id = current_user.id
    if not user_id:
        response = {"status": "500"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=500,
            mimetype="application/json",
        )
    chats = Chats.query.filter(
        or_(Chats.first_member_id == user_id, Chats.second_member_id == user_id)
    ).all()
    response = {"status": 200, "chats": []}
    for chat in chats:
        if chat.first_member_id == user_id:
            opponent = Users.query.filter_by(id=chat.second_member_id).first()
        else:
            opponent = Users.query.filter_by(id=chat.first_member_id).first()
        data = {
            "chat_id": chat.id,
            "opponent_name": " ".join(opponent.name.split()[:2]),
            "opponent_img": opponent.img,
            "opponent_id": opponent.id,
            "last_message": chat.last_message,
            "message_date": ":".join(chat.last_message_date.split(":")[:2])
            if chat.last_message_date
            else "",
            "is_read": chat.is_read,
            "unread_count": chat.unread_count,
            "unread_user_id": chat.unread_user_id,
        }
        if chat.last_message:
            response["chats"].append(data)
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/all_messages/", methods=["GET"])
@cross_origin()
@token_required
def get_all_message(current_user):
    chat_id = request.args.get("chat_id")
    user_id = current_user.id
    chat = Chats.query.filter_by(id=chat_id).first()
    if not user_id:
        response = {"status": "500", "text": "Not user"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=500,
            mimetype="application/json",
        )
    if user_id != chat.first_member_id and user_id != chat.second_member_id:
        response = {"status": "403", "text": "Is not a member"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=403,
            mimetype="application/json",
        )
    messages = Messages.query.filter_by(chat_id=chat_id).all()

    response = {"status": 200, "messages": []}
    chat.unread_count = 0
    chat.is_read = True
    db.session.add(chat)
    db.session.flush()
    db.session.commit()
    db.session.refresh(chat)
    for message in messages:
        message.is_read = True
        db.session.commit()
        sender = Users.query.filter_by(id=message.sender_id).first()
        data = {
            "sender_id": sender.id,
            "sender": {"image": sender.img, "name": sender.name},
            "message": message.message,
            "date": message.send_date,
            "is_read": message.is_read,
        }
        response["messages"].append(data)
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/send_message", methods=["POST"])
@cross_origin()
@token_required
def send_message(current_user):
    user_id = current_user.id
    data = request.json
    dt_now = str(datetime.now().strftime("%H:%M"))
    message = Messages(
        chat_id=data["chat_id"],
        sender_id=user_id,
        recipient_id=data["recipient_id"],
        message=data["message"],
        media=None,
        send_date=dt_now,
        is_read=False,
    )
    sender = Users.query.filter_by(id=message.sender_id).first()
    db.session.add(message)
    db.session.flush()
    db.session.commit()
    db.session.refresh(message)
    chat = Chats.query.filter_by(id=data["chat_id"]).first()
    chat.last_message = data["message"]
    chat.last_message_date = dt_now
    chat.is_read = False
    chat.unread_count = 1 + int(chat.unread_count)
    chat.unread_user_id = int(data["recipient_id"])
    db.session.commit()
    current_message = Messages.query.filter_by(id=message.id).first()
    response = {
        "status": 200,
        "message": {
            "message_id": current_message.id,
            "sender_id": current_message.sender_id,
            "sender": {"image": sender.img, "name": sender.name},
            "recipient_id": current_message.recipient_id,
            "message": current_message.message,
            "date": current_message.send_date,
        },
    }
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/create_chat", methods=["POST"])
@cross_origin()
@token_required
def create_chat(current_user):
    user_id = current_user.id
    data = request.json
    created_chat = Chats.query.filter(
        and_(
            Chats.first_member_id == user_id,
            Chats.second_member_id == data["second_member_id"],
        )
    ).first()
    if created_chat:
        opponent = Users.query.filter_by(id=created_chat.second_member_id).first()
        response = {
            "status": 200,
            "data": {
                "chat_id": created_chat.id,
                "opponent": {
                    "opponent_id": created_chat.second_member_id,
                    "opponent_name": opponent.name,
                    "opponent_img": opponent.img,
                },
            },
        }
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=200,
            mimetype="application/json",
        )
    chat = Chats(
        first_member_id=user_id,
        second_member_id=data["second_member_id"],
        creation_date=datetime.now(),
        last_message=None,
        last_message_date=None,
        is_read=True,
        unread_count=0,
    )
    db.session.add(chat)
    db.session.flush()
    db.session.commit()
    db.session.refresh(chat)
    current_req = Chats.query.filter_by(id=chat.id).first()
    opponent = Users.query.filter_by(id=chat.second_member_id).first()
    response = {
        "status": 200,
        "data": {
            "chat_id": current_req.id,
            "opponent": {
                "opponent_id": current_req.second_member_id,
                "opponent_name": opponent.name,
                "opponent_img": opponent.img,
            },
        },
    }
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/new_messages", methods=["GET"])
@cross_origin()
@token_required
def get_new_messages(current_user):
    user_id = current_user.id
    unread_messages = Messages.query.filter(
        and_(Messages.recipient_id == user_id, Messages.is_read == False)
    ).all()
    response = {"status": 200, "messages": []}
    for message in unread_messages:
        sender = Users.query.filter_by(id=message.sender_id).first()
        data = {
            "chat_id": message.chat_id,
            "message_id": message.id,
            "sender_id": message.sender_id,
            "sender": {
                "image": sender.img,
                "name": sender.name,
            },
            "recipient_id": message.recipient_id,
            "message": message.message,
            "date": message.send_date,
            "is_read": message.is_read,
        }
        response["messages"].append(data)
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/all_users/", methods=["GET"])
@cross_origin()
@token_required
def get_all_user(current_user):
    key = request.args.get("key")
    users = Users.query.all()
    response = {"status": 200, "users": []}
    for user in users:
        if (key.isdigit and key in str(user.isu)) or (key.lower() in user.name.lower()):
            data = {
                "id": user.id,
                "name": user.name,
                "isu": user.isu,
                "role": user.role,
                "course": user.course,
                "faculty": user.faculty,
                "group": user.group,
                "img": user.img,
            }
            response["users"].append(data)
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/user/")
@cross_origin()
@token_required
def get_user(current_user):
    id = request.args.get("id")
    user = Users.query.filter_by(id=id).first()
    if not user:
        response = {"status": 404, "text": "User not found"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=404,
            mimetype="application/json",
        )
    response = {
        "status": 200,
        "user": {
            "id": user.id,
            "name": user.name,
            "isu": user.isu,
            "role": user.role,
            "course": user.course,
            "faculty": user.faculty,
            "group": user.group,
            "img": user.img,
        },
    }
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/message", methods=["DELETE"])
@token_required
def delete_message(current_user):
    id = request.args.get("id")
    message = Messages.query.filter_by(id=id).first()
    if not message:
        response = {"status": 404, "text": "Message not found"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=404,
            mimetype="application/json",
        )
    if message.sender_id == current_user.id:
        Messages.query.filter_by(id=id).delete()
        db.session.commit()
    response = {"status": 200}
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/api/chat", methods=["DELETE"])
@token_required
def delete_chat(current_user):
    id = request.args.get("id")
    chat = Chats.query.filter_by(id=id).first()
    if not chat:
        response = {"status": 404, "text": "Chat not found"}
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=404,
            mimetype="application/json",
        )
    if (
        chat.first_member_id == current_user.id
        or chat.second_member_id == current_user.id
    ):
        Chats.query.filter_by(id=id).delete()
        db.session.query(Messages).filter(Messages.chat_id == id).delete()
        db.session.commit()
    response = {"status": 200}
    return Response(
        response=json.dumps(response, ensure_ascii=False),
        status=200,
        mimetype="application/json",
    )


@application.route("/media/users/<int:image_id>")
def get_user_image(image_id):
    return send_file(f"{os.getcwd()}/media/users/{image_id}.jpg", mimetype="image/jpg")
