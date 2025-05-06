import logging
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from models import User, Book, Rating
import os

# Configure logging
logger = logging.getLogger(__name__)

def load_data_to_db(db):
    """
    Load sample data into the database.
    
    Args:
        db: SQLAlchemy database instance
    """
    try:
        # Load books
        logger.info("Loading sample books data...")
        load_books(db)
        
        # Load users
        logger.info("Loading sample users data...")
        load_users(db)
        
        # Load ratings
        logger.info("Loading sample ratings data...")
        load_ratings(db)
        
        # Update book ratings
        logger.info("Updating book ratings...")
        update_book_ratings(db)
        
        # Commit all changes
        db.session.commit()
        logger.info("All sample data loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        db.session.rollback()
        raise

def load_books(db):
    """Load sample books into the database."""
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
            {
                'isbn': '0061120081',
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'year_of_publication': '2006',
                'publisher': 'Harper Perennial Modern Classics',
                'image_url_s': 'https://images.gr-assets.com/books/1553383690s/2657.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1553383690m/2657.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1553383690l/2657.jpg'
            },
            {
                'isbn': '0141439513',
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'year_of_publication': '2002',
                'publisher': 'Penguin Books',
                'image_url_s': 'https://images.gr-assets.com/books/1320399351s/1885.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1320399351m/1885.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1320399351l/1885.jpg'
            },
            {
                'isbn': '0743273567',
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'year_of_publication': '2004',
                'publisher': 'Scribner',
                'image_url_s': 'https://images.gr-assets.com/books/1490528560s/4671.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1490528560m/4671.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1490528560l/4671.jpg'
            },
            {
                'isbn': '0451526538',
                'title': 'Romeo and Juliet',
                'author': 'William Shakespeare',
                'year_of_publication': '2004',
                'publisher': 'Signet Classics',
                'image_url_s': 'https://images.gr-assets.com/books/1572098085s/18135.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1572098085m/18135.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1572098085l/18135.jpg'
            },
            {
                'isbn': '0142000671',
                'title': 'Of Mice and Men',
                'author': 'John Steinbeck',
                'year_of_publication': '2002',
                'publisher': 'Penguin Books',
                'image_url_s': 'https://images.gr-assets.com/books/1511302904s/890.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1511302904m/890.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1511302904l/890.jpg'
            },
            {
                'isbn': '0071122303',
                'title': 'The Hobbit',
                'author': 'J.R.R. Tolkien',
                'year_of_publication': '1937',
                'publisher': 'HarperCollins',
                'image_url_s': 'https://images.gr-assets.com/books/1546071216s/5907.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1546071216m/5907.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1546071216l/5907.jpg'
            },
            {
                'isbn': '0679783261',
                'title': 'Brave New World',
                'author': 'Aldous Huxley',
                'year_of_publication': '1998',
                'publisher': 'Vintage Classics',
                'image_url_s': 'https://images.gr-assets.com/books/1575509280s/5129.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1575509280m/5129.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1575509280l/5129.jpg'
            },
            {
                'isbn': '1400032717',
                'title': 'The Kite Runner',
                'author': 'Khaled Hosseini',
                'year_of_publication': '2004',
                'publisher': 'Riverhead Books',
                'image_url_s': 'https://images.gr-assets.com/books/1579036753s/77203.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1579036753m/77203.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1579036753l/77203.jpg'
            },
            {
                'isbn': '0452284244',
                'title': 'The Giver',
                'author': 'Lois Lowry',
                'year_of_publication': '2002',
                'publisher': 'Laurel Leaf Books',
                'image_url_s': 'https://images.gr-assets.com/books/1342493368s/3636.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1342493368m/3636.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1342493368l/3636.jpg'
            },
            {
                'isbn': '0143039431',
                'title': 'The Grapes of Wrath',
                'author': 'John Steinbeck',
                'year_of_publication': '2006',
                'publisher': 'Penguin Classics',
                'image_url_s': 'https://images.gr-assets.com/books/1552426897s/18114322.jpg',
                'image_url_m': 'https://images.gr-assets.com/books/1552426897m/18114322.jpg',
                'image_url_l': 'https://images.gr-assets.com/books/1552426897l/18114322.jpg'
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
        logger.info(f"Loaded {len(books)} sample books")
        
    except Exception as e:
        logger.error(f"Error loading sample books: {str(e)}")
        raise

def load_users(db):
    """Load sample users into the database."""
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
            },
            {
                'id': 276728,
                'username': 'user_276728',
                'email': 'user_276728@example.com',
                'password_hash': generate_password_hash('password123'),
                'location': 'Tokyo, Japan',
                'age': 26
            },
            {
                'id': 276729,
                'username': 'user_276729',
                'email': 'user_276729@example.com',
                'password_hash': generate_password_hash('password123'),
                'location': 'Paris, France',
                'age': 42
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
        logger.info(f"Loaded {len(users)} sample users")
        
    except Exception as e:
        logger.error(f"Error loading sample users: {str(e)}")
        raise

def load_ratings(db):
    """Load sample ratings into the database."""
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
            {'user_id': 276727, 'isbn': '1400032717', 'rating': 9},
            
            {'user_id': 276728, 'isbn': '0439023521', 'rating': 10},
            {'user_id': 276728, 'isbn': '0452284244', 'rating': 8},
            {'user_id': 276728, 'isbn': '0143039431', 'rating': 7},
            
            {'user_id': 276729, 'isbn': '0061120081', 'rating': 9},
            {'user_id': 276729, 'isbn': '0141439513', 'rating': 10},
            {'user_id': 276729, 'isbn': '0743273567', 'rating': 8}
        ]
        
        # Add each rating to the database
        ratings = []
        for rating_data in sample_ratings:
            rating = Rating(**rating_data, timestamp=datetime.utcnow())
            ratings.append(rating)
        
        db.session.add_all(ratings)
        db.session.flush()
        
        # Log progress
        logger.info(f"Loaded {len(ratings)} sample ratings")
        
    except Exception as e:
        logger.error(f"Error loading sample ratings: {str(e)}")
        raise

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
