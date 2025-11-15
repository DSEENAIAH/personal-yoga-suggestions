from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('Session', backref='user', lazy=True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Integer, nullable=False)
    sequence_id = db.Column(db.Integer, db.ForeignKey('sequence.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    duration = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Asana(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sanskrit_name = db.Column(db.String(100))
    overview_image = db.Column(db.String(200))
    step_data = db.Column(db.Text)  # JSON string
    difficulty = db.Column(db.String(20))
    benefits = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    intensity_min = db.Column(db.Integer, default=1)
    intensity_max = db.Column(db.Integer, default=5)
    asana_sequence = db.Column(db.Text)  # JSON array of asana IDs with durations
    total_duration = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('Session', backref='sequence', lazy=True)