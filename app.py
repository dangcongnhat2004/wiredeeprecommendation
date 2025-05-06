import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "booklovers-secret-key")

# Configure database to use PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Import models, forms and utils after db initialization to avoid circular imports
from models import User, Book, Rating, UserLibrary
from forms import LoginForm, RegisterForm, RatingForm
from data_loader import load_data_to_db

# We'll import RecommendationEngine only when needed to avoid TensorFlow issues
recommendation_engine = None

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Function to initialize the app
def initialize_app():
    """Initialize the application by creating DB tables and loading data."""
    global recommendation_engine
    
    try:
        # Create all tables
        with app.app_context():
            db.create_all()
            
            # Check if data needs to be loaded
            if db.session.query(Book).count() == 0:
                logger.info("No books found in database. Loading data from CSV files...")
                load_data_to_db(db)
                logger.info("Data loaded successfully!")
        
        # Initialize recommendation engine with fallback mechanism
        logger.info("Initializing recommendation engine...")
        try:
            # Import here instead of at the top level to avoid TensorFlow import issues
            from recommendation import RecommendationEngine
            recommendation_engine = RecommendationEngine()
            logger.info("Recommendation engine initialized!")
        except ImportError as e:
            logger.error(f"Could not import recommendation module: {str(e)}")
            recommendation_engine = None
        except Exception as e:
            logger.error(f"Error initializing recommendation engine: {str(e)}")
            # Set recommendation_engine to None to ensure the app still works
            recommendation_engine = None
    
    except Exception as e:
        logger.error(f"Error during app initialization: {str(e)}")
        # Continue running the app with minimum functionality

# Initialize the app at startup
initialize_app()

@app.route('/')
def index():
    """Home page with featured books."""
    # Get some popular books to display
    popular_books = Book.query.order_by(Book.avg_rating.desc()).limit(12).all()
    
    # If user is logged in, get personalized recommendations
    recommended_books = []
    if current_user.is_authenticated and recommendation_engine:
        try:
            # Get user recommendations
            recommended_ids = recommendation_engine.get_recommendations_for_user(current_user.id)
            recommended_books = Book.query.filter(Book.isbn.in_(recommended_ids)).limit(8).all()
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            flash("Could not load personalized recommendations.", "warning")
    
    # If no recommendations or user not logged in, show top-rated books
    if not recommended_books:
        recommended_books = Book.query.order_by(Book.avg_rating.desc()).limit(8).all()
    
    # Get recently added books
    recent_books = Book.query.order_by(Book.id.desc()).limit(8).all()
    
    return render_template('index.html', 
                          popular_books=popular_books,
                          recommended_books=recommended_books,
                          recent_books=recent_books)

@app.route('/books')
def books():
    """Browse books page with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    # Get filter parameters
    author = request.args.get('author', '')
    publisher = request.args.get('publisher', '')
    year = request.args.get('year', '')
    search = request.args.get('search', '')
    
    # Build query
    query = db.session.query(Book)
    
    if search:
        query = query.filter(Book.title.ilike(f'%{search}%') | 
                             Book.author.ilike(f'%{search}%') |
                             Book.isbn.ilike(f'%{search}%'))
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    if publisher:
        query = query.filter(Book.publisher.ilike(f'%{publisher}%'))
    if year:
        query = query.filter(Book.year_of_publication == year)
    
    # Execute paginated query
    pagination = query.paginate(page=page, per_page=per_page)
    books = pagination.items
    
    # Get distinct authors and publishers for filters
    authors = db.session.query(Book.author).distinct().order_by(Book.author).limit(100).all()
    publishers = db.session.query(Book.publisher).distinct().order_by(Book.publisher).limit(100).all()
    years = db.session.query(Book.year_of_publication).distinct().order_by(Book.year_of_publication.desc()).all()
    
    return render_template('books.html', 
                          books=books, 
                          pagination=pagination,
                          authors=authors,
                          publishers=publishers,
                          years=years,
                          current_filters={
                              'author': author,
                              'publisher': publisher,
                              'year': year,
                              'search': search
                          })

@app.route('/book/<isbn>')
def book_details(isbn):
    """Book details page."""
    book = Book.query.filter_by(isbn=isbn).first_or_404()
    
    # Get the book's ratings
    ratings = Rating.query.filter_by(isbn=isbn).order_by(Rating.timestamp.desc()).limit(10).all()
    
    # Check if user has rated this book
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(isbn=isbn, user_id=current_user.id).first()
    
    # Rating form
    form = RatingForm()
    if user_rating:
        form.rating.data = user_rating.rating
    
    # Get similar books if recommendation engine is available
    similar_books = []
    if recommendation_engine:
        try:
            similar_isbns = recommendation_engine.get_similar_books(isbn)
            similar_books = Book.query.filter(Book.isbn.in_(similar_isbns)).limit(6).all()
        except Exception as e:
            logger.error(f"Error getting similar books: {str(e)}")
    
    return render_template('book_details.html', 
                          book=book,
                          ratings=ratings,
                          user_rating=user_rating,
                          form=form,
                          similar_books=similar_books)

@app.route('/book/<isbn>/rate', methods=['POST'])
@login_required
def rate_book(isbn):
    """Rate a book."""
    book = Book.query.filter_by(isbn=isbn).first_or_404()
    form = RatingForm()
    
    if form.validate_on_submit():
        rating_value = form.rating.data
        
        # Check if user has already rated this book
        rating = Rating.query.filter_by(user_id=current_user.id, isbn=isbn).first()
        
        if rating:
            # Update existing rating
            rating.rating = rating_value
            rating.timestamp = datetime.utcnow()
            db.session.commit()
            flash('Your rating has been updated!', 'success')
        else:
            # Create new rating
            new_rating = Rating(
                user_id=current_user.id,
                isbn=isbn,
                rating=rating_value,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_rating)
            db.session.commit()
            flash('Your rating has been submitted!', 'success')
        
        # Update book's average rating
        update_book_avg_rating(isbn)
        
        return redirect(url_for('book_details', isbn=isbn))
    
    flash('Invalid rating submission.', 'danger')
    return redirect(url_for('book_details', isbn=isbn))

def update_book_avg_rating(isbn):
    """Update a book's average rating."""
    ratings = Rating.query.filter_by(isbn=isbn).all()
    if ratings:
        avg = sum(r.rating for r in ratings) / len(ratings)
        book = Book.query.filter_by(isbn=isbn).first()
        book.avg_rating = avg
        book.num_ratings = len(ratings)
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('register.html', form=form)
        
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            location=form.location.data,
            age=form.age.data
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    # Get user's ratings
    user_ratings = Rating.query.filter_by(user_id=current_user.id).order_by(Rating.timestamp.desc()).all()
    
    # Get books for these ratings
    rated_books = {}
    for rating in user_ratings:
        book = Book.query.filter_by(isbn=rating.isbn).first()
        if book:
            rated_books[rating.isbn] = book
    
    # Get personalized recommendations if recommendation engine is available
    recommended_books = []
    if recommendation_engine:
        try:
            recommended_ids = recommendation_engine.get_recommendations_for_user(current_user.id)
            recommended_books = Book.query.filter(Book.isbn.in_(recommended_ids)).limit(12).all()
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            flash("Could not load personalized recommendations.", "warning")
    
    return render_template('profile.html', 
                          user=current_user,
                          ratings=user_ratings,
                          rated_books=rated_books,
                          recommended_books=recommended_books)

@app.route('/add_to_library/<isbn>')
@login_required
def add_to_library(isbn):
    """Add a book to user's library."""
    book = Book.query.filter_by(isbn=isbn).first_or_404()
    
    # Check if book is already in library
    existing = UserLibrary.query.filter_by(user_id=current_user.id, isbn=isbn).first()
    
    if existing:
        flash('This book is already in your library!', 'info')
    else:
        # Add book to library
        library_entry = UserLibrary(
            user_id=current_user.id,
            isbn=isbn,
            added_on=datetime.utcnow()
        )
        db.session.add(library_entry)
        db.session.commit()
        flash('Book added to your library!', 'success')
    
    return redirect(url_for('book_details', isbn=isbn))

@app.route('/remove_from_library/<isbn>')
@login_required
def remove_from_library(isbn):
    """Remove a book from user's library."""
    library_entry = UserLibrary.query.filter_by(user_id=current_user.id, isbn=isbn).first_or_404()
    
    db.session.delete(library_entry)
    db.session.commit()
    
    flash('Book removed from your library!', 'success')
    return redirect(url_for('profile'))

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler."""
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler."""
    return render_template('error.html', error_code=500, message="Server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
