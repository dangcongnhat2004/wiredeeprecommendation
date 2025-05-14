link dataset:https://www.kaggle.com/datasets/ruchi798/bookcrossing-dataset?fbclid=IwY2xjawKRkgJleHRuA2FlbQIxMABicmlkETFjcE45RGMzNlJiU1VrYVMxAR4QxYgiQRUKPWc-fTKUnj2xNpEISn5RThh4aqUchVly_hre4k-iW1OZ8xtDBQ_aem_SdLaIozo3IfuzQELNTWLGw









how to run this app?
step 1:
      stage:config:
      download dataset includes 3 file move all to instance foleder on this project
step 2: 
      stage:run:
      on your terminal of project : flask run 
Book Recommendation System - System Overview

This document provides an overview of the Book Recommendation System, a web application designed to help users discover books and receive personalized recommendations.
1. Core Functionality

    User Authentication:

        Users can register for new accounts.

        Registered users can log in and log out.

        Session management with "Remember Me" functionality.

    Book Browsing and Searching:

        Display a catalog of books.

        Search books by title, author, or ISBN.

        Filter books by author, publisher, and year of publication.

        Pagination for browsing large lists of books.

    Book Details:

        View detailed information for each book, including title, author, publisher, year, cover image, average rating, and number of ratings.

        Display recent ratings for the book.

    Book Rating:

        Authenticated users can rate books on a scale of 1-10.

        Users can update their existing ratings.

    User Library:

        Authenticated users can add books to their personal library.

        Users can remove books from their library.

    User Profile:

        View user's registration details (username, email, location, age).

        Display a list of books rated by the user.

        Display books in the user's personal library.

    Book Recommendations:

        Personalized Recommendations (for logged-in users):

            Utilizes a pre-trained Wide & Deep neural network model (if TensorFlow is available and the model is loaded successfully).

            Considers user's age, past rated books, and book features (author, publisher, year, ratings statistics) to predict interaction scores.

            Recommends books with the highest predicted scores that the user has not yet rated.

            Caches recommendations per user for faster subsequent requests.

        Similar Book Recommendations:

            For a given book, recommends other similar books.

            If the Wide & Deep model is available, similarity is computed based on encoded book features (author, publisher, year, scaled ratings). Note: The current _compute_similarity in recommendation.py is a simple feature overlap; a more sophisticated method using model embeddings would be ideal but is not fully implemented for this.

        Fallback Recommendation Strategies:

            If TensorFlow/Model is unavailable or for new users with no ratings:

                Personalized Fallback (User-Based Collaborative Filtering): If a user has rated some books, the system finds other users with similar rating patterns and recommends books highly rated by those similar users (but not yet rated by the current user).

                Popular Books Fallback: If no personalized recommendations can be generated (e.g., new user, no similar users found), the system recommends popular books based on high average ratings and a minimum number of ratings. This is also used as a general fallback.

                Similar Books Fallback (Metadata-based): If the model isn't available, similar books are found based on matching author, then publisher, then year, and finally by general high ratings.

        Featured Books on Homepage:

            Displays popular books.

            Displays personalized recommendations for logged-in users (or top-rated books as fallback).

            Displays recently added books.

2. System Architecture and Technologies

    Backend Framework: Flask (Python)

    Database: SQLite (managed via Flask-SQLAlchemy ORM)

    Authentication: Flask-Login

    Forms: Flask-WTF

    Recommendation Engine (recommendation.py):

        Primary Model: Pre-trained Wide & Deep neural network model (Keras/TensorFlow).

            Attempts to load model and associated encoders (for user ID, ISBN, author, publisher, year, age bin) and a scaler for item features from attached_assets/ or models/ directory.

            Uses pickle to load encoders and scaler.

        Libraries (Attempted Lazy Import): TensorFlow, Keras, NumPy, Pandas. The system is designed to function with fallback mechanisms if these are not available.

        Fallback Logic: Implements simpler recommendation methods (collaborative filtering, popularity-based, metadata-based similarity) if the primary neural model cannot be loaded or if required libraries are missing.

    Data Loading (data_loader.py):

        Loads initial book, user, and rating data from CSV files (BX_Books.csv, BX-Users.csv, BX-Book-Ratings.csv) located in a dataset/ directory.

        Includes fallback to load sample data if CSV files are not found.

        Preprocesses user data (e.g., generating usernames, emails, hashing default passwords, parsing age).

        Calculates and updates average ratings and number of ratings for books.

    Models (models.py): Defines SQLAlchemy ORM models for User, Book, Rating, and UserLibrary.

    Utilities (utils.py): Helper functions for image URLs, location formatting, text truncation, and admin user creation.

    Admin User: A default admin user can be created for administrative purposes (password configurable via environment variable or defaults to admin123).

3. Data Model

    User: id, username, email, password_hash, location, age, registration_date.

    Book: id, isbn, title, author, year_of_publication, publisher, image_url_s, image_url_m, image_url_l, avg_rating, num_ratings.

    Rating: id, user_id (FK to User), isbn (FK to Book), rating (1-10), timestamp.

    UserLibrary: id, user_id (FK to User), isbn (FK to Book), added_on.

4. Key Features of the Recommendation Logic

    Lazy Loading of ML Libraries: TensorFlow, Keras, NumPy, and Pandas are imported on-demand by the RecommendationEngine to allow the web application to start and function with basic features even if these heavy libraries are not installed or encounter issues.

    Model and Encoder Loading: The system attempts to load pre-trained model artifacts. The paths are hardcoded but with a primary and alternative location.

    Feature Encoding for Model: Includes methods to encode raw user and book data into the numerical format expected by the Wide & Deep model using pre-loaded LabelEncoder and MinMaxScaler objects.

    Fallback for Unknown Entities: Encoding methods provide default values (e.g., 0) for users, books, authors, etc., not seen during the encoder's training.

    Caching: Basic caching for user recommendations, book features, and similar books is implemented to improve performance.

    Error Handling and Logging: Logging is used throughout the recommendation engine to track operations and errors. Fallback mechanisms are designed to provide a degraded but functional service.

    Prediction without Title Embeddings: The _predict_score method in recommendation.py currently prepares inputs for the Wide & Deep model by adding dummy zero-vector title embeddings (np.zeros((1, 50))). This means the live prediction does not currently use the Word2Vec title embeddings that were part of the model training in recomendation_wide_and_deep.ipynb. This is a significant simplification/discrepancy compared to the training notebook.

5. Setup and Running

    Requires Python and Flask.

    Database (SQLite) will be created automatically in an instance/ directory.

    Dataset CSV files should be placed in a dataset/ directory at the root of the project for initial data loading.

    Pre-trained model (wide_deep_book_model_top50k.keras) and associated .pkl encoder/scaler files should be placed in attached_assets/ (primary) or models/ (secondary) for the recommendation engine to load.

    To run the application: python main.py (or flask run after setting FLASK_APP=app.py).

6. Potential Areas for Improvement (as suggested by code structure)

    Full integration of Word2Vec title embeddings into the live prediction pipeline of RecommendationEngine.

    More sophisticated similarity computation in _compute_similarity for model-based similar book recommendations (e.g., using item embeddings from the Wide & Deep model).

    Enhanced error handling and more robust fallback strategies.

    Configuration management for file paths instead of hardcoding.

    More advanced caching strategies.

    Asynchronous task execution for long-running recommendation computations.
