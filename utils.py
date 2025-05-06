import logging
from werkzeug.security import generate_password_hash
import os

# Configure logging
logger = logging.getLogger(__name__)

def get_default_image(size='s'):
    """
    Get default image URL for books without images.
    
    Args:
        size: Image size ('s', 'm', or 'l')
    
    Returns:
        Default image URL
    """
    if size == 's':
        return "https://via.placeholder.com/60x80?text=No+Cover"
    elif size == 'm':
        return "https://via.placeholder.com/100x140?text=No+Cover"
    else:  # 'l'
        return "https://via.placeholder.com/200x280?text=No+Cover"

def format_location(location):
    """
    Format location string.
    
    Args:
        location: Raw location string
    
    Returns:
        Formatted location string
    """
    if not location or location == "Unknown":
        return "Unknown"
    
    parts = location.split(', ')
    if len(parts) == 1:
        return parts[0]
    elif len(parts) >= 2:
        city, country = parts[0], parts[-1]
        return f"{city}, {country}"
    else:
        return location

def truncate_text(text, max_length=100):
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def create_admin_user(db, User):
    """
    Create admin user if it doesn't exist.
    
    Args:
        db: SQLAlchemy database instance
        User: User model class
    """
    try:
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Create admin user
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Default password for demo
            hashed_password = generate_password_hash(admin_password)
            
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=hashed_password,
                location='Admin Location',
                age=30
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logger.info("Admin user created successfully")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.session.rollback()
