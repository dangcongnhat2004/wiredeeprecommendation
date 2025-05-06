from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address'),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=1, max=120)])
    submit = SubmitField('Register')

class RatingForm(FlaskForm):
    """Form for rating a book."""
    rating = SelectField('Rating', choices=[
        (0, 'Select a rating'),
        (1, '1 - Poor'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5 - Average'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10 - Excellent')
    ], coerce=int, validators=[
        DataRequired(),
        NumberRange(min=1, max=10, message='Please select a rating between 1 and 10')
    ])
    submit = SubmitField('Submit Rating')

class SearchForm(FlaskForm):
    """Form for searching books."""
    search = StringField('Search', validators=[Optional()])
    author = StringField('Author', validators=[Optional()])
    publisher = StringField('Publisher', validators=[Optional()])
    year = StringField('Year', validators=[Optional()])
    submit = SubmitField('Search')
