from flask import Flask, render_template, session, redirect, url_for, g, request
# import random
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import MovieForm, ScoreForm, YearForm, RegistrationForm, LoginForm, ReviewForm, UpdateUsernameForm
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
@login_required
def cart():
    db = get_db()
    user_id = session["user_id"]

    watchlist = db.execute("""
        SELECT movies.*, watchlist.count 
        FROM watchlist
        JOIN movies ON watchlist.movie_id = movies.movie_id
        WHERE watchlist.user_id = ?
    """, (user_id,)).fetchall()

    return render_template("watchlist.html", watchlist=watchlist)

@app.route("/add_to_watchlist/<int:movie_id>")
@login_required
def add_to_watchlist(movie_id):
    db = get_db()
    user_id = session["user_id"]

    movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
    if not movie:
        return "Movie not found.", 404

    existing_watchlist_item = db.execute(
        "SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?",
        (user_id, movie_id)
    ).fetchone()

    if existing_watchlist_item:
        db.execute(
            "UPDATE watchlist SET count = count + 1 WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        )
    else:
        db.execute(
            "INSERT INTO watchlist (user_id, movie_id, count) VALUES (?, ?, 1)",
            (user_id, movie_id)
        )

    db.commit()
    return redirect(url_for("random_movie"))

@app.route("/clear_watchlist")
@login_required
def clear_watchlist():
    db = get_db()
    user_id = session["user_id"]

    db.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
    db.commit()

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

    existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
    if existing_user:
        return "Username already exists. Please choose a different one.", 400

    db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", (new_username, session["user_id"]))
    db.commit()

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

@app.route('/user', methods=["GET", "POST"])
@login_required
def user():
    db = get_db()
    user_id = session.get("user_id")
    form = UpdateUsernameForm()

    if form.validate_on_submit():
        new_username = form.username.data

        existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
        if existing_user:
            form.username.errors.append("Username already exists. Please choose a different one.")
        else:
            db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", (new_username, user_id))
            db.commit()

            session["user_id"] = new_username
            session.modified = True

            return redirect(url_for("user"))

    reviews = db.execute("""
        SELECT reviews.*, movies.title 
        FROM reviews 
        JOIN movies ON reviews.movie_id = movies.movie_id 
        WHERE reviews.user = ?
    """, (user_id,)).fetchall()

    return render_template('user.html', form=form, reviews=reviews)

# adding stuff

# @app.route("/follow/<username>")
# @login_required
# def follow_user(username):
#     db = get_db()
#     current_user = session["user_id"]

#     # Check if the user exists
#     user_to_follow = db.execute("SELECT * FROM users WHERE user_id = ?", (username,)).fetchone()
#     if not user_to_follow:
#         return "User not found.", 404

#     # Check if the current user is already following the target user
#     existing_follow = db.execute(
#         "SELECT * FROM network WHERE follower = ? AND following = ?",
#         (current_user, username)
#     ).fetchone()

#     if existing_follow:
#         return "You are already following this user.", 400

#     # Add the follow relationship
#     db.execute(
#         "INSERT INTO network (follower, following) VALUES (?, ?)",
#         (current_user, username)
#     )
#     db.commit()

#     return redirect(url_for("user_profile", username=username))

# @app.route("/unfollow/<username>")
# @login_required
# def unfollow_user(username):
#     db = get_db()
#     current_user = session["user_id"]

#     # Remove the follow relationship
#     db.execute(
#         "DELETE FROM network WHERE follower = ? AND following = ?",
#         (current_user, username)
#     )
#     db.commit()

#     return redirect(url_for("user_profile", username=username))

# @app.route("/user/<username>")
# @login_required
# def user_profile(username):
#     db = get_db()

#     # Fetch the user's details
#     user = db.execute("SELECT * FROM users WHERE user_id = ?", (username,)).fetchone()
#     if not user:
#         return "User not found.", 404

#     # Fetch the user's reviews
#     reviews = db.execute("""
#         SELECT reviews.*, movies.title 
#         FROM reviews 
#         JOIN movies ON reviews.movie_id = movies.movie_id 
#         WHERE reviews.user = ?
#     """, (username,)).fetchall()

#     # Fetch followers and following
#     followers = db.execute(
#         "SELECT follower FROM network WHERE following = ?",
#         (username,)
#     ).fetchall()

#     following = db.execute(
#         "SELECT following FROM network WHERE follower = ?",
#         (username,)
#     ).fetchall()

#     # Check if the current user is following this user
#     is_following = db.execute(
#         "SELECT * FROM network WHERE follower = ? AND following = ?",
#         (session["user_id"], username)
#     ).fetchone() is not None

#     return render_template(
#         "user_profile.html",
#         user=user,
#         reviews=reviews,
#         followers=followers,
#         following=following,
#         is_following=is_following
#     )

# needs changing 

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found. Please check if there was an error with how the link was typed up.</p>"

@app.errorhandler(405)
def handle_exception(e):
    return "<h1>405 Method not Allowed</h1><p>The server has received the request but rejected the specific HTTP method used please try again</p>"

@app.errorhandler(500)
def handle_exception(e):
    return "<h1>500 Internal Server Error</h1><p>The server encountered an unexpected condition that prevented it from fulfilling the request</p>"

@app.errorhandler(403)
def handle_exception(e):
    return "<h1>403 Forbidden</h1><p>The request you have made is forbidden</p>"

if __name__ == "__main__":
    app.run(debug=True)
