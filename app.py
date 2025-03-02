from flask import Flask, render_template, session, redirect, url_for, g, request
# import random
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import MovieForm, ScoreForm, YearForm, RegistrationForm, LoginForm, ReviewForm
from functools import wraps

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "jordansPw"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id",None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return(redirect(url_for("login", next=request.url)))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/random", methods=["GET", "POST"])
@login_required
def random_movie():
    db = get_db()
    movie = db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1").fetchone()
    
    form = ReviewForm()

    if form.validate_on_submit():
        review_text = form.review_text.data
        rating = form.rating.data
        user = session.get("user_id", "Anonymous")  # Use logged-in user or Anonymous

        db.execute(
            "INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
            (movie["movie_id"], user, review_text, rating),
        )
        db.commit()


        return redirect(url_for("random_movie"))

    reviews = db.execute("SELECT * FROM reviews WHERE movie_id = ?", (movie["movie_id"],)).fetchall()

    return render_template("random.html", movie=movie, reviews=reviews, form=form)


@app.route("/recommendations", methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
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
@login_required
def year_search():
    form = YearForm()
    movies = None
    if form.validate_on_submit():
        year = form.year.data
        db = get_db()
        movies = db.execute("SELECT * FROM movies WHERE year = ?", (year,)).fetchall()
    return render_template("year.html", form=form,
                            movies=movies)

@app.route("/watchlist")
def cart():
    if "watchlist" not in session:
        session["watchlist"] = {}
        session.modified = True
    return render_template("watchlist.html", 
                           watchlist=session["watchlist"])

@app.route("/add_to_watchlist/<int:movie_id>")
def add_to_watchlist(movie_id):
    if "watchlist" not in session:
        session["watchlist"] = {}
    if movie_id not in session["watchlist"]:
        session["watchlist"][movie_id] = 1
    else:
        session["watchlist"][movie_id] = session["watchlist"][movie_id] + 1
    session.modified = True
    return redirect(url_for("cart"))

@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
@login_required
def movie_details(movie_id):
    db = get_db()
    form = ReviewForm()
    
    if form.validate_on_submit():
        review_text = form.review_text.data
        rating = form.rating.data
        user = "Anonymous"
        db.execute("INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
                   (movie_id, user, review_text, rating))
        db.commit()
    
    movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE movie_id = ?", (movie_id,)).fetchall()

    return render_template("reviews.html", movie=movie, 
                           reviews=reviews, 
                           form=form)

@app.route("/edit_username", methods=["POST"])
@login_required
def edit_username():
    new_username = request.form.get("new_username")
    db = get_db()

    # Check if the new username already exists
    existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
    if existing_user:
        return "Username already exists. Please choose a different one.", 400

    # Update the username in the database
    db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", (new_username, session["user_id"]))
    db.commit()

    # Update the session with the new username
    session["user_id"] = new_username
    session.modified = True

    return redirect(url_for("index"))

@app.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()

        user_in_db = db.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,)).fetchone()
        if user_in_db:
            form.user_id.errors.append("User ID already exists! Please choose a different one.")
        else:
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (user_id, password) VALUES (?, ?);", (user_id, hashed_password))
            db.commit()
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user_in_db = db.execute("""
                SELECT * FROM users
                WHERE user_id = ?;""", (user_id,)).fetchone()
        if user_in_db is None:
            form.user_id.errors.append("No such user name!")
        elif not check_password_hash (
                user_in_db["password"],password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = user_id
            session.modified = True
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    session.modified = True 
    return redirect( url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
