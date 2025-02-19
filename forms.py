from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, FloatField, IntegerField
from wtforms.validators import InputRequired, NumberRange

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
