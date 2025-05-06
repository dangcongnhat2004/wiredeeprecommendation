from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication and user data."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    location = db.Column(db.String(100))
    age = db.Column(db.Integer)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('Rating', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    library = db.relationship('UserLibrary', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    """Book model with book details."""
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    year_of_publication = db.Column(db.String(10))
    publisher = db.Column(db.String(255))
    image_url_s = db.Column(db.String(255))  # Small image URL
    image_url_m = db.Column(db.String(255))  # Medium image URL
    image_url_l = db.Column(db.String(255))  # Large image URL
    avg_rating = db.Column(db.Float, default=0.0)
    num_ratings = db.Column(db.Integer, default=0)
    
    # Relationships
    ratings = db.relationship('Rating', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    library_entries = db.relationship('UserLibrary', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Book {self.title} ({self.isbn})>'

class Rating(db.Model):
    """Rating model for user book ratings."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    isbn = db.Column(db.String(20), db.ForeignKey('book.isbn'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating value
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to ensure a user can only rate a book once
    __table_args__ = (db.UniqueConstraint('user_id', 'isbn', name='_user_book_rating_uc'),)
    
    def __repr__(self):
        return f'<Rating User:{self.user_id} Book:{self.isbn} Rating:{self.rating}>'

class UserLibrary(db.Model):
    """User's book library model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    isbn = db.Column(db.String(20), db.ForeignKey('book.isbn'), nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to ensure a book can only be in a user's library once
    __table_args__ = (db.UniqueConstraint('user_id', 'isbn', name='_user_book_library_uc'),)
    
    def __repr__(self):
        return f'<UserLibrary User:{self.user_id} Book:{self.isbn}>'
