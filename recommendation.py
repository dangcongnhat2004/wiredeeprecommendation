import os
import pickle
import logging
from sqlalchemy import func
from models import User, Book, Rating

# Configure logging
logger = logging.getLogger(__name__)

# Flag to indicate if TensorFlow is available
TF_AVAILABLE = False
tf = None
keras = None
np = None
pd = None

# We'll try importing these libraries only when needed
def _try_import_libraries():
    global TF_AVAILABLE, tf, keras, np, pd
    if TF_AVAILABLE:
        return True  # Already imported successfully
        
    try:
        # First try to import numpy and pandas
        import numpy
        import pandas
        np = numpy
        pd = pandas
        
        # Then try TensorFlow
        import tensorflow
        from tensorflow import keras as keras_module
        tf = tensorflow
        keras = keras_module
        TF_AVAILABLE = True
        logger.info("Successfully imported TensorFlow and dependencies")
        return True
    except ImportError as e:
        logger.warning(f"Could not import required libraries: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error importing libraries: {str(e)}")
        return False

class RecommendationEngine:
    """
    Handles book recommendations using the pre-trained wide & deep model.
    Loads encoders from .pkl files and model from .keras file.
    """
    
    def __init__(self):
        """Initialize the recommendation engine by loading models and encoders."""
        try:
            # Initialize default values for all attributes
            self.model = None
            self.user_id_encoder = None
            self.isbn_encoder = None
            self.author_encoder = None
            self.publisher_encoder = None
            self.year_encoder = None
            self.age_bin_encoder = None
            self.item_scaler = None
            
            # Initialize cache for faster recommendations
            self.user_cache = {}
            self.book_cache = {}
            self.similar_books_cache = {}
            
            # Try to import TensorFlow and dependencies
            if not _try_import_libraries():
                logger.warning("Required libraries not available, using fallback recommendations only")
                return
            
            # Create models directory if it doesn't exist
            os.makedirs('models', exist_ok=True)
            
            # Try to load the model from attached_assets
            try:
                model_path = 'attached_assets/wide_deep_book_model_top50k.keras'
                if os.path.exists(model_path):
                    self.model = keras.models.load_model(model_path)
                    logger.info("Keras model loaded successfully from attached_assets")
                else:
                    logger.warning(f"Model file not found at {model_path}, checking alternative location")
                    alt_path = 'models/wide_deep_book_model_top50k.keras'
                    if os.path.exists(alt_path):
                        self.model = keras.models.load_model(alt_path)
                        logger.info("Keras model loaded successfully from models directory")
                    else:
                        logger.error("Model file not found in any location")
            except Exception as e:
                logger.error(f"Error loading Keras model: {str(e)}")
                logger.warning("Operating in fallback mode without neural model")
            
            # Build cache for faster recommendations
            self.user_cache = {}
            self.book_cache = {}
            self.similar_books_cache = {}
            
            logger.info("Recommendation engine initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing recommendation engine: {str(e)}")
            raise
    
    def _load_encoder(self, path):
        """Load an encoder from pickle file."""
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading encoder {path}: {str(e)}")
            # Return empty encoder as fallback
            return None
    
    def get_recommendations_for_user(self, user_id, top_n=24):
        """
        Get book recommendations for a user.
        
        Args:
            user_id: User ID
            top_n: Number of recommendations to return
            
        Returns:
            List of recommended book ISBNs
        """
        from app import db
        
        # Check cache first
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        try:
            # If model is not available, use collaborative filtering fallback
            if self.model is None:
                return self._get_recommendations_fallback(user_id, top_n)
            
            # Get user data
            user = db.session.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return self._get_popular_books(top_n)
            
            # Get user's rated books
            user_ratings = db.session.query(Rating).filter(Rating.user_id == user_id).all()
            rated_isbns = {rating.isbn for rating in user_ratings}
            
            if not rated_isbns:
                # If user hasn't rated any books, return popular books
                return self._get_popular_books(top_n)
            
            # Get all books
            books = db.session.query(Book).all()
            
            # Filter out books the user has already rated
            candidate_books = [book for book in books if book.isbn not in rated_isbns]
            
            # If no candidates, return popular books
            if not candidate_books:
                return self._get_popular_books(top_n)
            
            # Prepare user features
            user_features = {
                'user_id': self._encode_user_id(user_id),
                'age_bin': self._encode_age_bin(user.age if user.age else 0)
            }
            
            # Predict scores for all candidate books
            scores = []
            for book in candidate_books:
                # Get book features
                book_features = self._get_book_features(book)
                
                # Combine features
                features = {**user_features, **book_features}
                
                # Predict score
                score = self._predict_score(features)
                scores.append((book.isbn, score))
            
            # Sort by score in descending order
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get top_n recommendations
            recommendations = [isbn for isbn, _ in scores[:top_n]]
            
            # Cache results
            self.user_cache[user_id] = recommendations
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return self._get_popular_books(top_n)
    
    def _get_recommendations_fallback(self, user_id, top_n=24):
        """Fallback recommendation method using collaborative filtering."""
        from app import db
        
        try:
            # Get user's rated books
            user_ratings = db.session.query(Rating).filter(Rating.user_id == user_id).all()
            if not user_ratings:
                return self._get_popular_books(top_n)
            
            # Find users with similar taste
            similar_users = set()
            for rating in user_ratings:
                # Find other users who rated this book similarly
                similar_ratings = db.session.query(Rating).filter(
                    Rating.isbn == rating.isbn,
                    Rating.user_id != user_id,
                    Rating.rating >= rating.rating - 1,  # Similar rating threshold
                    Rating.rating <= rating.rating + 1
                ).all()
                
                similar_users.update([r.user_id for r in similar_ratings])
            
            if not similar_users:
                return self._get_popular_books(top_n)
            
            # Get books rated highly by similar users but not rated by current user
            rated_isbns = {r.isbn for r in user_ratings}
            
            # Get all ratings from similar users for books the current user hasn't rated
            similar_ratings = db.session.query(Rating).filter(
                Rating.user_id.in_(similar_users),
                ~Rating.isbn.in_(rated_isbns),
                Rating.rating >= 7  # Only consider highly rated books
            ).all()
            
            # Count frequency of each book
            book_counts = {}
            for rating in similar_ratings:
                if rating.isbn in book_counts:
                    book_counts[rating.isbn] += 1
                else:
                    book_counts[rating.isbn] = 1
            
            # Sort by frequency
            sorted_books = sorted(book_counts.items(), key=lambda x: x[1], reverse=True)
            recommendations = [isbn for isbn, _ in sorted_books[:top_n]]
            
            # If not enough recommendations, add popular books
            if len(recommendations) < top_n:
                popular_books = self._get_popular_books(top_n - len(recommendations))
                recommendations.extend([isbn for isbn in popular_books if isbn not in recommendations])
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error in fallback recommendation: {str(e)}")
            return self._get_popular_books(top_n)
    
    def _get_popular_books(self, limit=24):
        """Get popular books based on ratings."""
        from app import db
        
        try:
            # Get books with highest average rating and at least 5 ratings
            popular_books = db.session.query(Book.isbn).filter(
                Book.num_ratings >= 5
            ).order_by(
                Book.avg_rating.desc()
            ).limit(limit).all()
            
            return [book.isbn for book in popular_books]
        
        except Exception as e:
            logger.error(f"Error getting popular books: {str(e)}")
            # As a last resort, get random books
            return db.session.query(Book.isbn).limit(limit).all()
    
    def get_similar_books(self, isbn, top_n=6):
        """
        Get books similar to a given book.
        
        Args:
            isbn: Book ISBN
            top_n: Number of similar books to return
            
        Returns:
            List of similar book ISBNs
        """
        from app import db
        
        # Check cache first
        if isbn in self.similar_books_cache:
            return self.similar_books_cache[isbn]
        
        try:
            # Get book
            book = db.session.query(Book).filter(Book.isbn == isbn).first()
            if not book:
                logger.warning(f"Book {isbn} not found")
                return []
            
            # If model is not available, use metadata-based similarity
            if self.model is None:
                return self._get_similar_books_fallback(book, top_n)
            
            # Get all books
            books = db.session.query(Book).filter(Book.isbn != isbn).all()
            
            # Get book features for the target book
            target_features = self._get_book_features(book)
            
            # Compute similarity scores
            scores = []
            for other_book in books:
                # Get book features
                other_features = self._get_book_features(other_book)
                
                # Compute similarity (simple feature overlap for now)
                similarity = self._compute_similarity(target_features, other_features)
                scores.append((other_book.isbn, similarity))
            
            # Sort by similarity in descending order
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get top_n similar books
            similar_books = [isbn for isbn, _ in scores[:top_n]]
            
            # Cache results
            self.similar_books_cache[isbn] = similar_books
            
            return similar_books
        
        except Exception as e:
            logger.error(f"Error getting similar books for {isbn}: {str(e)}")
            return self._get_similar_books_fallback(book, top_n)
    
    def _get_similar_books_fallback(self, book, top_n=6):
        """Fallback method for finding similar books based on metadata."""
        from app import db
        
        try:
            # Find books with same author
            same_author = db.session.query(Book).filter(
                Book.author == book.author,
                Book.isbn != book.isbn
            ).order_by(
                Book.avg_rating.desc()
            ).limit(top_n).all()
            
            similar_isbns = [b.isbn for b in same_author]
            
            # If not enough, find books from same publisher
            if len(similar_isbns) < top_n:
                same_publisher = db.session.query(Book).filter(
                    Book.publisher == book.publisher,
                    Book.isbn != book.isbn,
                    ~Book.isbn.in_(similar_isbns)
                ).order_by(
                    Book.avg_rating.desc()
                ).limit(top_n - len(similar_isbns)).all()
                
                similar_isbns.extend([b.isbn for b in same_publisher])
            
            # If still not enough, find books from same year
            if len(similar_isbns) < top_n:
                same_year = db.session.query(Book).filter(
                    Book.year_of_publication == book.year_of_publication,
                    Book.isbn != book.isbn,
                    ~Book.isbn.in_(similar_isbns)
                ).order_by(
                    Book.avg_rating.desc()
                ).limit(top_n - len(similar_isbns)).all()
                
                similar_isbns.extend([b.isbn for b in same_year])
            
            # If still not enough, add highly rated books
            if len(similar_isbns) < top_n:
                highly_rated = db.session.query(Book).filter(
                    Book.isbn != book.isbn,
                    ~Book.isbn.in_(similar_isbns)
                ).order_by(
                    Book.avg_rating.desc()
                ).limit(top_n - len(similar_isbns)).all()
                
                similar_isbns.extend([b.isbn for b in highly_rated])
            
            return similar_isbns
        
        except Exception as e:
            logger.error(f"Error in fallback similar books: {str(e)}")
            # Last resort: return random books
            return db.session.query(Book.isbn).filter(
                Book.isbn != book.isbn
            ).limit(top_n).all()
    
    def _encode_user_id(self, user_id):
        """Encode user ID using the pre-trained encoder."""
        if self.user_id_encoder is None:
            return 0
        
        try:
            # Check if user_id is in the encoder's vocabulary
            if user_id in self.user_id_encoder.classes_:
                return self.user_id_encoder.transform([user_id])[0]
            else:
                return 0  # Default encoding for unknown users
        except Exception as e:
            logger.error(f"Error encoding user ID: {str(e)}")
            return 0
    
    def _encode_isbn(self, isbn):
        """Encode ISBN using the pre-trained encoder."""
        if self.isbn_encoder is None:
            return 0
        
        try:
            # Check if isbn is in the encoder's vocabulary
            if isbn in self.isbn_encoder.classes_:
                return self.isbn_encoder.transform([isbn])[0]
            else:
                return 0  # Default encoding for unknown books
        except Exception as e:
            logger.error(f"Error encoding ISBN: {str(e)}")
            return 0
    
    def _encode_author(self, author):
        """Encode author using the pre-trained encoder."""
        if self.author_encoder is None:
            return 0
        
        try:
            # Check if author is in the encoder's vocabulary
            if author in self.author_encoder.classes_:
                return self.author_encoder.transform([author])[0]
            else:
                return 0  # Default encoding for unknown authors
        except Exception as e:
            logger.error(f"Error encoding author: {str(e)}")
            return 0
    
    def _encode_publisher(self, publisher):
        """Encode publisher using the pre-trained encoder."""
        if self.publisher_encoder is None:
            return 0
        
        try:
            # Check if publisher is in the encoder's vocabulary
            if publisher in self.publisher_encoder.classes_:
                return self.publisher_encoder.transform([publisher])[0]
            else:
                return 0  # Default encoding for unknown publishers
        except Exception as e:
            logger.error(f"Error encoding publisher: {str(e)}")
            return 0
    
    def _encode_year(self, year):
        """Encode year using the pre-trained encoder."""
        if self.year_encoder is None:
            return 0
        
        try:
            # Check if year is in the encoder's vocabulary
            if year in self.year_encoder.classes_:
                return self.year_encoder.transform([year])[0]
            else:
                return 0  # Default encoding for unknown years
        except Exception as e:
            logger.error(f"Error encoding year: {str(e)}")
            return 0
    
    def _encode_age_bin(self, age):
        """Encode age bin using the pre-trained encoder."""
        if self.age_bin_encoder is None:
            return 0
        
        try:
            # Bin the age
            if age <= 0:
                age_bin = 'Unknown'
            elif age < 18:
                age_bin = 'Under 18'
            elif age < 25:
                age_bin = '18-24'
            elif age < 35:
                age_bin = '25-34'
            elif age < 45:
                age_bin = '35-44'
            elif age < 55:
                age_bin = '45-54'
            elif age < 65:
                age_bin = '55-64'
            else:
                age_bin = '65+'
            
            # Check if age_bin is in the encoder's vocabulary
            if age_bin in self.age_bin_encoder.classes_:
                return self.age_bin_encoder.transform([age_bin])[0]
            else:
                return 0  # Default encoding for unknown age bins
        except Exception as e:
            logger.error(f"Error encoding age bin: {str(e)}")
            return 0
    
    def _get_book_features(self, book):
        """Get features for a book."""
        try:
            # Check cache first
            if book.isbn in self.book_cache:
                return self.book_cache[book.isbn]
            
            features = {
                'isbn': self._encode_isbn(book.isbn),
                'author': self._encode_author(book.author),
                'publisher': self._encode_publisher(book.publisher),
                'year': self._encode_year(book.year_of_publication)
            }
            
            # Scale features if scaler is available
            if self.item_scaler is not None:
                # Add dummy features for scaling
                to_scale = {
                    'avg_rating': book.avg_rating,
                    'num_ratings': book.num_ratings
                }
                
                # Scale features
                scaled = self.item_scaler.transform([[
                    to_scale['avg_rating'], 
                    to_scale['num_ratings']
                ]])
                
                features['avg_rating_scaled'] = scaled[0][0]
                features['num_ratings_scaled'] = scaled[0][1]
            else:
                # Simple normalization as fallback
                features['avg_rating_scaled'] = book.avg_rating / 10
                features['num_ratings_scaled'] = min(book.num_ratings / 100, 1.0)
            
            # Cache results
            self.book_cache[book.isbn] = features
            
            return features
        
        except Exception as e:
            logger.error(f"Error getting book features for {book.isbn}: {str(e)}")
            # Return default features
            return {
                'isbn': 0,
                'author': 0,
                'publisher': 0,
                'year': 0,
                'avg_rating_scaled': 0.5,
                'num_ratings_scaled': 0.0
            }
    
    def _predict_score(self, features):
        """Predict score for a user-book pair."""
        try:
            # If model or numpy is not available, return default score
            if self.model is None or np is None:
                # Fallback scoring
                return 0.5  # Default score
            
            # Try to import TensorFlow and dependencies if not already available
            if not TF_AVAILABLE and not _try_import_libraries():
                return 0.5  # Default score if libraries cannot be imported
            
            # Prepare input data for the model
            inputs = {
                'user_id_encoded': np.array([features['user_id']]),
                'isbn_encoded': np.array([features['isbn']]),
                'author_encoded': np.array([features['author']]),
                'publisher_encoded': np.array([features['publisher']]),
                'year_encoded': np.array([features['year']]),
                'age_binned_encoded': np.array([features['age_bin']]),
                'avg_rating_scaled': np.array([features['avg_rating_scaled']]),
                'num_ratings_scaled': np.array([features['num_ratings_scaled']])
            }
            
            # For deep part, we need to add dummy title embedding
            inputs['title_embedding_features'] = np.zeros((1, 50))  # Assuming 50-dim embeddings
            
            # Make prediction
            prediction = self.model.predict(inputs, verbose=0)
            
            return prediction[0][0]  # Return scalar value
        
        except Exception as e:
            logger.error(f"Error predicting score: {str(e)}")
            return 0.5  # Default score
    
    def _compute_similarity(self, features1, features2):
        """Compute similarity between two feature sets."""
        try:
            # Simple similarity measure based on feature overlap
            author_match = features1['author'] == features2['author']
            publisher_match = features1['publisher'] == features2['publisher']
            year_match = features1['year'] == features2['year']
            
            # Weighted sum of matches (author is most important)
            similarity = (
                2.0 * author_match +
                1.0 * publisher_match + 
                0.5 * year_match
            ) / 3.5
            
            # Boost by ratings similarity
            rating_diff = abs(features1['avg_rating_scaled'] - features2['avg_rating_scaled'])
            similarity *= (1.0 - 0.5 * rating_diff)
            
            return similarity
        
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0  # Default similarity
