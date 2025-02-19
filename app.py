from flask import Flask, render_template, request
import random
from database import get_db, close_db
from flask_session import Session
from forms import MovieForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "this"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.teardown_appcontext(close_db)

@app.route("/")
def index():
    form = MovieForm()
    return render_template("index.html", 
                           form=form)

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
    return render_template("genre.html",
                            form=form,
                            movies=movies)

@app.route("/score", methods=["GET", "POST"])
def score_search():
    if request.method == "POST":
        min_score = request.form.get("min_score", type=float)
        max_score = request.form.get("max_score", type=float)
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE score BETWEEN ? AND ?", (min_score, max_score)).fetchall()
        return render_template("score.html",
                                movies=movies)
    return render_template("score.html")

@app.route("/year", methods=["GET", "POST"])
def year_search():
    if request.method == "POST":
        year = request.form.get("year", type=int)
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE year = ?", (year,)).fetchall()
        return render_template("year.html",
                                movies=movies)
    return render_template("year.html")