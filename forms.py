from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import InputRequired

class MovieForm(FlaskForm):
    genre = SelectField("Genre", choices=[
        ("Sci-Fi", "Sci-Fi"),
        ("Action", "Action"),
        ("Crime", "Crime"),
        ("Drama", "Drama"),
        ("Fantasy","Fantasy"),
        ("Thriller","Thriller"),
        ("Horror","Horror")
    ], validators=[InputRequired()])
    submit = SubmitField("Get Recommendations")