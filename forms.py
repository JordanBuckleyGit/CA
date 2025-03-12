from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FloatField, IntegerField, TextAreaField, PasswordField, BooleanField, FileField
from wtforms.validators import InputRequired, NumberRange, EqualTo

class SearchForm(FlaskForm):
    search = StringField("Search for a movie:")
    submit = SubmitField("Search")

class MovieForm(FlaskForm):
    genre = SelectField("Genre", choices=[
        ("Sci-Fi", "Sci-Fi"),
        ("Action", "Action"),
        ("Crime", "Crime"),
        ("Drama", "Drama"),
        ("Fantasy", "Fantasy"),
        ("Thriller", "Thriller"),
        ("Horror", "Horror"),
        ("Comedy", "Comedy")
    ], validators=[InputRequired()])
    submit = SubmitField("Get Recommendations")

class ScoreForm(FlaskForm):
    min_score = FloatField("Min Score", validators=[InputRequired(), NumberRange(min=0, max=10)])
    max_score = FloatField("Max Score", validators=[InputRequired(), NumberRange(min=0, max=10)])
    submit = SubmitField("Search by Score")

class YearForm(FlaskForm):
    year = IntegerField("Year", validators=[InputRequired(), NumberRange(min=1900, max=2100)])
    submit = SubmitField("Search by Year")

class RegistrationForm(FlaskForm):
    user_id = StringField("User id:",
                    validators=[InputRequired()])
    password = PasswordField("Password:",
                    validators=[InputRequired()])
    password2 = PasswordField("Repeat Password:",
                    validators=[InputRequired(),
                                EqualTo("password")])
    is_admin = BooleanField("Is Admin")
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    user_id = StringField("User id:",
                    validators=[InputRequired()])
    password = PasswordField("Password:",
                    validators=[InputRequired()])
    submit = SubmitField("Submit")
    
class ReviewForm(FlaskForm):
    review_text = TextAreaField("Your Review", validators=[InputRequired()])
    rating = IntegerField("Rating (1-10)", validators=[InputRequired(), NumberRange(min=1, max=10)])
    submit = SubmitField("Submit Review")

class UpdateUsernameForm(FlaskForm):
    username = StringField("New Username", validators=[InputRequired()])
    submit = SubmitField("Update Username")

class MovieSuggestionForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    genre = SelectField("Genre", choices=[
        ("Sci-Fi", "Sci-Fi"),
        ("Action", "Action"),
        ("Crime", "Crime"),
        ("Drama", "Drama"),
        ("Fantasy", "Fantasy"),
        ("Thriller", "Thriller"),
        ("Horror", "Horror"),
        ("Comedy", "Comedy")
    ], validators=[InputRequired()])
    score = FloatField("Score", validators=[InputRequired(), NumberRange(min=0, max=10)])
    year = IntegerField("Year", validators=[InputRequired(), NumberRange(min=1900, max=2100)])
    director = StringField("Director", validators=[InputRequired()])
    description = TextAreaField("Description", validators=[InputRequired()])
    image = FileField("Movie Image", validators=[InputRequired()])
    submit = SubmitField("Submit Suggestion")

class TicketForm(FlaskForm):
    question = TextAreaField("Your Question", validators=[InputRequired()])
    submit = SubmitField("Submit Ticket")

class AdminResponseForm(FlaskForm):
    response = TextAreaField("Admin Response", validators=[InputRequired()])
    submit = SubmitField("Submit Response")
