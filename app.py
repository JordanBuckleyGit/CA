from flask import Flask, render_template, request
import random
from database import get_db, close_db
from flask_session import Session
from forms import MovieForm, ScoreForm, YearForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "jordansPw"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.teardown_appcontext(close_db)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/random")
def random_movie():
    db = get_db()
    movie = db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1").fetchone()
    return render_template("random.html",
                            movie=movie)

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    form = MovieForm()
    movies = None
    if form.validate_on_submit():
        genre = form.genre.data
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE genre = ?", (genre,)).fetchall()
    return render_template("recommendations.html",
                            movies=movies)

@app.route("/genre", methods=["GET", "POST"])
def genre_search():
    form = MovieForm()
    movies = None
    if form.validate_on_submit():
        genre = form.genre.data
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE genre = ?", (genre,)).fetchall()
    return render_template("genre.html", form=form,
                            movies=movies)

@app.route("/score", methods=["GET", "POST"])
def score_search():
    form = ScoreForm()
    movies = None
    if form.validate_on_submit():
        min_score = form.min_score.data
        max_score = form.max_score.data
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE score BETWEEN ? AND ?", (min_score, max_score)).fetchall()
    return render_template("score.html", form=form,
                            movies=movies)

@app.route("/year", methods=["GET", "POST"])
def year_search():
    form = YearForm()
    movies = None
    if form.validate_on_submit():
        year = form.year.data
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE year = ?", (year,)).fetchall()
    return render_template("year.html", form=form,
                            movies=movies)

# @app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
# def movie_details(movie_id):
#     db = get_db()
#     form = ReviewForm()
    
#     if form.validate_on_submit():
#         review_text = form.review_text.data
#         rating = form.rating.data
#         user = "Anonymous"  # Replace with user authentication if available
#         db.execute("INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
#                    (movie_id, user, review_text, rating))
#         db.commit()
    
#     movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
#     reviews = db.execute("SELECT * FROM reviews WHERE movie_id = ?", (movie_id,)).fetchall()

#     return render_template("reviews.html", movie=movie, 
#                            reviews=reviews, 
#                            form=form)
