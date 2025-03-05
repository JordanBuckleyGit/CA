from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FloatField, IntegerField, TextAreaField, PasswordField, BooleanField
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
        ("Horror", "Horror")
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