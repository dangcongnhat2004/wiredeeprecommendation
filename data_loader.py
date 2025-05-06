import logging
import csv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from models import User, Book, Rating

# Configure logging
logger = logging.getLogger(__name__)

def load_data_to_db(db):
    """
    Load data from CSV files into the database.
    
    Args:
        db: SQLAlchemy database instance
    """
    try:
        # Load books
        logger.info("Loading books data from CSV...")
        load_books(db)
        
        # Load users
        logger.info("Loading users data from CSV...")
        load_users(db)
        
        # Load ratings
        logger.info("Loading ratings data from CSV...")
        load_ratings(db)
        
        # Update book ratings
        logger.info("Updating book ratings...")
        update_book_ratings(db)
        
        # Commit all changes
        db.session.commit()
        logger.info("All data loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        db.session.rollback()
        raise

def load_books(db):
    """Load books from BX_Books.csv into the database."""
    try:
        # Check if the file exists
        csv_path = 'dataset/BX_Books.csv'
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}")
            logger.warning("Using fallback sample data for books")
            _load_sample_books(db)
            return
            
        # Open the CSV file
        with open(csv_path, 'r', encoding='ISO-8859-1', errors='replace') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            # Process each row
            count = 0
            batch_size = 1000
            books = []
            
            for row in reader:
                # Skip if ISBN is missing
                if not row.get('ISBN'):
                    continue
                
                # Create book object
                book = Book(
                    isbn=row.get('ISBN', ''),
                    title=row.get('Book-Title', 'Unknown Title'),
                    author=row.get('Book-Author', 'Unknown Author'),
                    year_of_publication=row.get('Year-Of-Publication', ''),
                    publisher=row.get('Publisher', 'Unknown Publisher'),
                    image_url_s=row.get('Image-URL-S', ''),
                    image_url_m=row.get('Image-URL-M', ''),
                    image_url_l=row.get('Image-URL-L', '')
                )
                
                # Add to batch
                books.append(book)
                count += 1
                
                # Commit in batches
                if len(books) >= batch_size:
                    db.session.add_all(books)
                    db.session.flush()
                    logger.info(f"Loaded {count} books")
                    books = []
            
            # Add remaining books
            if books:
                db.session.add_all(books)
                db.session.flush()
            
            # Log progress
            logger.info(f"Loaded {count} books in total")
        
    except Exception as e:
        logger.error(f"Error loading books: {str(e)}")
        logger.warning("Using fallback sample data for books")
        _load_sample_books(db)

def _load_sample_books(db):
    """Load sample books as fallback."""
    try:
        # Sample book data
        sample_books = [
            {
                'isbn': '0316066524',
                'title': 'The Twilight Saga Collection',
                'author': 'Stephenie Meyer',
                'year_of_publication': '2009',
                'publisher': 'Little, Brown and Company',
                'image_url_s': 'https://images.gr-assets.com/books/1361039443s/6377550.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1361039443m/6377550.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1361039443l/6377550.jpg'
            },
            {
                'isbn': '0439023521',
                'title': 'The Hunger Games',
                'author': 'Suzanne Collins',
                'year_of_publication': '2010',
                'publisher': 'Scholastic Press',
                'image_url_s': 'https://images.gr-assets.com/books/1586722975s/2767052.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1586722975m/2767052.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1586722975l/2767052.jpg'
            },
            # Thêm 10 quyển sách khác ở đây
            {
                'isbn': '0061120081',
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'year_of_publication': '2006',
                'publisher': 'Harper Perennial Modern Classics',
                'image_url_s': 'https://images.gr-assets.com/books/1553383690s/2657.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1553383690m/2657.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1553383690l/2657.jpg'
            }
        ]
        
        # Add each book to the database
        books = []
        for book_data in sample_books:
            book = Book(**book_data)
            books.append(book)
        
        db.session.add_all(books)
        db.session.flush()
        
        # Log progress
        logger.info(f"Loaded {len(books)} sample books as fallback")
    except Exception as e:
        logger.error(f"Error loading sample books: {str(e)}")

def load_users(db):
    """Load users from BX_Users.csv into the database."""
    try:
        # Check if the file exists
        csv_path = 'dataset/BX-Users.csv'
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}")
            logger.warning("Using fallback sample data for users")
            _load_sample_users(db)
            return
            
        # Open the CSV file
        with open(csv_path, 'r', encoding='ISO-8859-1', errors='replace') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            # Process each row
            count = 0
            batch_size = 1000
            users = []
            
            # Generate a default password hash for all users
            default_password = 'password123'  # For demo purposes
            password_hash = generate_password_hash(default_password)
            
            for row in reader:
                # Skip if user ID is missing
                if not row.get('User-ID'):
                    continue
                
                # Extract data
                user_id = int(row.get('User-ID', 0))
                location = row.get('Location', '')
                
                # Parse age (safely)
                age = None
                try:
                    age_str = row.get('Age', '')
                    if age_str and age_str.isdigit():
                        age = int(age_str)
                        # Filter out unreasonable ages
                        if age < 5 or age > 100:
                            age = None
                except (ValueError, TypeError):
                    age = None
                
                # Generate username and email
                username = f"user_{user_id}"
                email = f"user_{user_id}@example.com"
                
                # Create user object
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    location=location,
                    age=age,
                    registration_date=datetime.utcnow()
                )
                
                # Add to batch
                users.append(user)
                count += 1
                
                # Commit in batches
                if len(users) >= batch_size:
                    db.session.add_all(users)
                    db.session.flush()
                    logger.info(f"Loaded {count} users")
                    users = []
            
            # Add remaining users
            if users:
                db.session.add_all(users)
                db.session.flush()
            
            # Log progress
            logger.info(f"Loaded {count} users in total")
        
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        logger.warning("Using fallback sample data for users")
        _load_sample_users(db)

def _load_sample_users(db):
    """Load sample users as fallback."""
    try:
        # Sample user data
        sample_users = [
            {
                'id': 276725,
                'username': 'user_276725',
                'email': 'user_276725@example.com',
                'password_hash': generate_password_hash('password123'),
                'location': 'New York, USA',
                'age': 32
            },
            {
                'id': 276726,
                'username': 'user_276726',
                'email': 'user_276726@example.com',
                'password_hash': generate_password_hash('password123'),
                'location': 'London, UK',
                'age': 28
            },
            {
                'id': 276727,
                'username': 'user_276727',
                'email': 'user_276727@example.com',
                'password_hash': generate_password_hash('password123'),
                'location': 'Sydney, Australia',
                'age': 35
            }
        ]
        
        # Add each user to the database
        users = []
        for user_data in sample_users:
            user = User(**user_data, registration_date=datetime.utcnow())
            users.append(user)
        
        db.session.add_all(users)
        db.session.flush()
        
        # Log progress
        logger.info(f"Loaded {len(users)} sample users as fallback")
    except Exception as e:
        logger.error(f"Error loading sample users: {str(e)}")

def load_ratings(db):
    """Load ratings from BX-Book-Ratings.csv into the database."""
    try:
        # Check if the file exists
        csv_path = 'dataset/BX-Book-Ratings.csv'
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}")
            logger.warning("Using fallback sample data for ratings")
            _load_sample_ratings(db)
            return
            
        # Get valid users and books
        valid_users = {user.id for user in db.session.query(User.id).all()}
        valid_books = {book.isbn for book in db.session.query(Book.isbn).all()}
        
        if not valid_users or not valid_books:
            logger.warning("No valid users or books found in database")
            logger.warning("Using fallback sample data for ratings")
            _load_sample_ratings(db)
            return
            
        # Open the CSV file
        with open(csv_path, 'r', encoding='ISO-8859-1', errors='replace') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            # Process each row
            count = 0
            batch_size = 5000
            ratings = []
            
            for row in reader:
                # Skip if user ID or ISBN is missing
                if not row.get('User-ID') or not row.get('ISBN'):
                    continue
                
                # Extract and validate data
                try:
                    user_id = int(row.get('User-ID', 0))
                    isbn = row.get('ISBN', '')
                    rating_value = int(row.get('Book-Rating', 0))
                    
                    # Skip zero ratings (they're "not rated" in the dataset)
                    if rating_value == 0:
                        continue
                    
                    # Skip if user or book doesn't exist
                    if user_id not in valid_users or isbn not in valid_books:
                        continue
                    
                    # Create rating object
                    rating = Rating(
                        user_id=user_id,
                        isbn=isbn,
                        rating=rating_value,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Add to batch
                    ratings.append(rating)
                    count += 1
                    
                    # Commit in batches
                    if len(ratings) >= batch_size:
                        db.session.add_all(ratings)
                        db.session.flush()
                        logger.info(f"Loaded {count} ratings")
                        ratings = []
                        
                except (ValueError, TypeError) as e:
                    # Skip invalid data
                    continue
            
            # Add remaining ratings
            if ratings:
                db.session.add_all(ratings)
                db.session.flush()
            
            # Log progress
            logger.info(f"Loaded {count} ratings in total")
        
    except Exception as e:
        logger.error(f"Error loading ratings: {str(e)}")
        logger.warning("Using fallback sample data for ratings")
        _load_sample_ratings(db)

def _load_sample_ratings(db):
    """Load sample ratings as fallback."""
    try:
        # Sample rating data
        sample_ratings = [
            {'user_id': 276725, 'isbn': '0316066524', 'rating': 8},
            {'user_id': 276725, 'isbn': '0439023521', 'rating': 9},
            {'user_id': 276725, 'isbn': '0061120081', 'rating': 7},
            
            {'user_id': 276726, 'isbn': '0451526538', 'rating': 10},
            {'user_id': 276726, 'isbn': '0142000671', 'rating': 8},
            {'user_id': 276726, 'isbn': '0071122303', 'rating': 9},
            
            {'user_id': 276727, 'isbn': '0316066524', 'rating': 6},
            {'user_id': 276727, 'isbn': '0679783261', 'rating': 7},
            {'user_id': 276727, 'isbn': '1400032717', 'rating': 9}
        ]
        
        # Add each rating to the database
        ratings = []
        for rating_data in sample_ratings:
            rating = Rating(**rating_data, timestamp=datetime.utcnow())
            ratings.append(rating)
        
        db.session.add_all(ratings)
        db.session.flush()
        
        # Log progress
        logger.info(f"Loaded {len(ratings)} sample ratings as fallback")
    except Exception as e:
        logger.error(f"Error loading sample ratings: {str(e)}")

def update_book_ratings(db):
    """Update average ratings for all books."""
    try:
        # Get all books
        books = db.session.query(Book).all()
        
        for book in books:
            # Get all ratings for this book
            ratings = db.session.query(Rating).filter(Rating.isbn == book.isbn).all()
            
            if ratings:
                # Calculate average rating
                avg_rating = sum(r.rating for r in ratings) / len(ratings)
                book.avg_rating = avg_rating
                book.num_ratings = len(ratings)
        
        db.session.commit()
        logger.info(f"Updated average ratings for {len(books)} books")
        
    except Exception as e:
        logger.error(f"Error updating book ratings: {str(e)}")
        raise
