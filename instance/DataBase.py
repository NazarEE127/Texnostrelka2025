from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String, nullable=False)
    ava = db.Column(db.String, nullable=False)
    admin = db.Column(db.Integer)


class Routes(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    user_id = db.Column(db.Integer)
    rating = db.Column(db.String)
    status = db.Column(db.Integer)
    count_marks = db.Column(db.Integer, default=0)
    photos_id = db.Column(db.String)
    route_coords = db.Column(db.String)


class Comments(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    route_id = db.Column(db.Integer)
    text = db.Column(db.String)


class History(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    user_id = db.Column(db.Integer)
    rating = db.Column(db.String)
    status = db.Column(db.Integer)
    route_id = db.Column(db.Integer)
#    relevance = db.Column(db.Integer)


class Photos(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer)
    name = db.Column(db.String)


class Visit(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    route_id = db.Column(db.Integer)

