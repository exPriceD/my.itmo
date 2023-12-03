from config import db, UserMixin
from datetime import datetime


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(512))
    password = db.Column(db.String(512))
    name = db.Column(db.String(128))
    isu = db.Column(db.Integer)
    # img = db.Column(db.String(32768))

    def __init__(self, login, password, name, isu):
        self.login = login
        self.password = password
        self.name = name
        self.isu = isu

    def __repr__(self):
        return f'User {self.id}'


class Chats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_member_id = db.Column(db.Integer)
    second_member_id = db.Column(db.Integer)
    creation_date = db.Column(db.DateTime)
    last_message = db.Column(db.String(32768))
    last_message_date = db.Column(db.String(128))
    is_read = db.Column(db.Boolean)

    def __repr__(self):
        return f'Chat {self.id}'


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer)
    recipient_id = db.Column(db.Integer)
    message = db.Column(db.String(32768))
    media = db.Column(db.String(1024))
    send_date = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean)

    def __repr__(self):
        return f'Message {self.id}'
