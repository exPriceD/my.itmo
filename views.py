from config import application, db, login_manager
from models import Users, Chats, Messages
from flask import request, Response
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils import check_register_data, check_login_data
import json
import random
from sqlalchemy import or_


@login_manager.user_loader
def load_user(user_id):
    return Users.query.filter_by(id=user_id).first()


@application.route("/api/current_user", methods=["GET"])
@login_required
def current_user_id():
    response = {"id": current_user.id}
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')


@application.route("/api/login", methods=["POST"])
def login():
    if current_user.is_authenticated:
        response = {"status": "302", "text": "Already authenticated"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=302, mimetype='application/json')
    data = request.json
    try:
        if not check_login_data(data=data):
            response = {"status": "400"}
            return Response(response=json.dumps(response, ensure_ascii=False), status=400, mimetype='application/json')
        user = Users.query.filter_by(login=data["login"]).first()
        if check_password_hash(pwhash=user.password, password=data["password"]):
            login_user(user, remember=True)
            response = {"status": "200"}
            return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')
        response = {"status": "404"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=404, mimetype='application/json')
    except:
        response = {"status": "500"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=500, mimetype='application/json')


@application.route('/api/registration', methods=["POST"])
def registration():
    if current_user.is_authenticated:
        response = {"status": "302", "text": "Already authenticated"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=302, mimetype='application/json')
    data = request.json
    try:
        if not check_register_data(data=data):
            response = {"status": "400"}
            return Response(response=json.dumps(response, ensure_ascii=False), status=400, mimetype='application/json')
        pwhash = generate_password_hash(password=data["password"])
        generated_isu = random.randint(100000, 999999)
        user = Users(login=data["login"], password=pwhash, name=data["name"], isu=generated_isu)
        db.session.add(user)
        db.session.flush()
        db.session.commit()
        login_user(Users.query.filter_by(login=data["login"]).first())
        response = {"status": "200"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')
    except:
        response = {"status": "500"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=500, mimetype='application/json')


@application.route("/api/all_chats", methods=["GET"])
@login_required
def get_all_chats():
    user_id = current_user.id
    if not user_id:
        response = {"status": "500"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=500, mimetype='application/json')
    chats = Chats.query.filter(or_(Chats.first_member_id == user_id, Chats.second_member_id == user_id)).all()
    response = {"status": 200, "chats": []}
    for chat in chats:
        if chat.first_member_id == user_id:
            opponent = Users.query.filter_by(id=chat.second_member_id).first()
        else:
            opponent = Users.query.filter_by(id=chat.first_member_id).first()
        data = {
            chat.last_message_date: {
                "chat_id": chat.id,
                "opponent_name": opponent.name,  # добавить img base64
                "last_message": chat.last_message,
                "message_date": chat.last_message_date,
                "is_read": chat.is_read
            }
        }
        if chat.last_message:
            response["chats"].append(data)
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')


@application.route("/api/all_message/<int:chat_id>", methods=["GET"])
@login_required
def get_all_message(chat_id):
    user_id = current_user.id
    chat = Chats.query.filter_by(id=chat_id).first()
    if not user_id:
        response = {"status": "500", "text": "Not user"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=500, mimetype='application/json')
    if user_id != chat.first_member_id and user_id != chat.second_member_id:
        response = {"status": "500"}
        return Response(response=json.dumps(response, ensure_ascii=False), status=500, mimetype='application/json')
    messages = Messages.query.filter_by(chat_id=chat_id)
    response = {"status": 200, "messages": []}
    for message in messages:
        data = {
            message.send_date: {
                "sender_id": message.sender_id,
                "message": message.message,
                "date": message.send_date,
                "is_read": message.is_read
            }
        }
        response["messages"].append(data)
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')


@application.route('/api/send_message', methods=["POST"])
@login_required
def send_message():
    data = request.json
    message = Messages(
        chat_id=data["chat_id"],
        sender_id=data["sender_id"],
        recipient_id=data["recipient_id"],
        message=data["message"],
        media=None,
        is_read=False
    )
    db.session.add(message)
    db.session.flush()
    db.session.commit()
    chat = Chats.query.filter_by(id=data["chat_id"]).first()
    chat.last_message = data["message"]
    chat.last_message_date = str(datetime.now())
    chat.is_read = False
    db.session.commit()
    response = {"status": 200}
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')


@application.route('/api/create_chat', methods=["POST"])
@login_required
def create_chat():
    data = request.json
    chat = Chats(
        first_member_id=data["first_member_id"],
        second_member_id=data["second_member_id"],
        creation_date=datetime.now(),
        last_message=None,
        last_message_date=None,
        is_read=True
    )
    db.session.add(chat)
    db.session.flush()
    db.session.commit()
    db.session.refresh(chat)
    current_req = Chats.query.filter_by(id=chat.id).first()
    response = {
        "status": 200, "data": {
            "chat_id": current_req.id,
        }
    }
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')


@application.route("/api/all_users/<string:key>", methods=["GET"])
@login_required
def get_all_user(key: str):
    users = Users.query.all()
    response = {"status": 200, "users": []}
    for user in users:
        if (key.isdigit and key in str(user.isu)) or (key in user.name):
                data = {
                    "id": user.id,
                    "name": user.name,
                    "isu": user.isu
                }
                response["users"].append(data)
    return Response(response=json.dumps(response, ensure_ascii=False), status=200, mimetype='application/json')