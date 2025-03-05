from flask import Flask, render_template, session, redirect, url_for, g, request
# import random
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SearchForm,MovieForm, ScoreForm, YearForm, RegistrationForm, LoginForm, ReviewForm, UpdateUsernameForm
from functools import wraps

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "jordansPw"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# checkers 

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id")
    g.is_admin = session.get("is_admin", False) 

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return(redirect(url_for("login", next=request.url)))
        return view(*args, **kwargs)
    return wrapped_view

# Movie main stuff search routes

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    query = request.args.get('query', '').strip() 
    filter_type = request.args.get('filter', 'all')

    db = get_db()
    cur = db.cursor()

    if filter_type == 'genre':
        if query:
            cur.execute("SELECT * FROM movies WHERE genre LIKE ?", ('%' + query + '%',))
        else:
            cur.execute("SELECT * FROM movies")
        results = cur.fetchall()
        return render_template('search.html', results=results)
    elif filter_type == 'score':
        try:
            score_value = float(query)
            cur.execute("SELECT * FROM movies WHERE score >= ?", (score_value,))
            results = cur.fetchall()
            return render_template('search.html', results=results)
        except ValueError:
            cur.execute("SELECT * FROM movies")
            results = cur.fetchall()
            return render_template('search.html', results=results)
    elif filter_type == 'year':
        try:
            year_value = int(query)
            cur.execute("SELECT * FROM movies WHERE year = ?", (year_value,))
            results = cur.fetchall()
            return render_template('search.html', results=results)
        except ValueError:
            cur.execute("SELECT * FROM movies")
            results = cur.fetchall()
            return render_template('search.html', results=results)
    elif filter_type == 'highest_reviewed':
        cur.execute("""
            SELECT movies.*, AVG(reviews.rating) AS avg_rating
            FROM movies
            JOIN reviews ON movies.movie_id = reviews.movie_id
            GROUP BY movies.movie_id
            ORDER BY avg_rating DESC
            LIMIT 10
        """)
        results = cur.fetchall()
        return render_template('search.html', results=results)
    elif filter_type == 'all':
        cur.execute("SELECT * FROM movies")
        all_movies = cur.fetchall()

        movies_by_genre = {}
        for movie in all_movies:
            genre = movie['genre']
            if genre not in movies_by_genre:
                movies_by_genre[genre] = []
            movies_by_genre[genre].append(movie)

        return render_template('search.html', movies_by_genre=movies_by_genre)
    else:
        if query:
            cur.execute("SELECT * FROM movies WHERE title LIKE ?", ('%' + query + '%',))
        else:
            cur.execute("SELECT * FROM movies")
        results = cur.fetchall()
        return render_template('search.html', results=results)

@app.route("/random", methods=["GET", "POST"])
@login_required
def random_movie():
    db = get_db()
    form = ReviewForm()

    if request.method == "GET":
        movie = db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1").fetchone()
        session["random_movie_id"] = movie["movie_id"]
    else:
        movie_id = session.get("random_movie_id")
        if not movie_id:
            return "Error: No movie ID found in session. Please try again.", 400

        movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
        if not movie:
            return "Error: Movie not found. Please try again.", 404

    if form.validate_on_submit():
        review_text = form.review_text.data
        rating = form.rating.data
        user = session.get("user_id", "Anonymous")

        movie_id = session.get("random_movie_id")
        if not movie_id:
            return "Error: No movie ID found in session. Please try again.", 400

        db.execute(
            "INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
            (movie_id, user, review_text, rating),
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

# DNA SECTION
@app.route("/my-dna")
@login_required
def my_dna():
    db = get_db()
    user_id = session["user_id"]

    watchlist = db.execute("""
        SELECT movies.* 
        FROM watchlist
        JOIN movies ON watchlist.movie_id = movies.movie_id
        WHERE watchlist.user_id = ?
    """, (user_id,)).fetchall()

    watchlist = [dict(movie) for movie in watchlist]

    user_genres = {movie["genre"] for movie in watchlist}
    user_min_score = min((movie["score"] for movie in watchlist), default=0)

    highly_reviewed = db.execute("""
        SELECT movies.*, AVG(reviews.rating) AS avg_rating
        FROM movies
        JOIN reviews ON movies.movie_id = reviews.movie_id
        WHERE movies.genre IN ({})
        GROUP BY movies.movie_id
        HAVING avg_rating >= 8.0
        ORDER BY avg_rating DESC
    """.format(",".join("?" * len(user_genres))), tuple(user_genres)).fetchall()

    highly_reviewed = [dict(movie) for movie in highly_reviewed]

    unique_movies = {}

    for movie in watchlist:
        unique_movies[movie["movie_id"]] = movie

    for movie in highly_reviewed:
        if movie["movie_id"] not in unique_movies and movie["score"] >= user_min_score:
            unique_movies[movie["movie_id"]] = movie

    recommended_movies = list(unique_movies.values())

    return render_template("my_dna.html", movies=recommended_movies)

# Session cart/wishlist

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

# Review section

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

# User section 

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

# Login/register section

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

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user_in_db = db.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,)).fetchone()
        if user_in_db is None:
            form.user_id.errors.append("No such user name!")
        elif not check_password_hash(user_in_db["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = user_id
            session["is_admin"] = bool(user_in_db["is_admin"])  # Store is_admin in session
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

# admin login section

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    return render_template("admin_dashboard.html")

# admin movies

@app.route("/admin/manage_movies")
@login_required
def manage_movies():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    movies = db.execute("SELECT * FROM movies").fetchall()
    return render_template("manage_movies.html", movies=movies)

@app.route("/admin/delete_movie/<int:movie_id>")
@login_required
def delete_movie(movie_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    db.execute("DELETE FROM movies WHERE movie_id = ?", (movie_id,))
    db.commit()
    return redirect(url_for("manage_movies"))

@app.route("/admin/edit_movie/<int:movie_id>", methods=["GET", "POST"])
@login_required
def edit_movie(movie_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
    if request.method == "POST":
        title = request.form["title"]
        genre = request.form["genre"]
        score = float(request.form["score"])
        year = int(request.form["year"])
        director = request.form["director"]
        description = request.form["description"]
        db.execute(
            "UPDATE movies SET title = ?, genre = ?, score = ?, year = ?, director = ?, description = ? WHERE movie_id = ?",
            (title, genre, score, year, director, description, movie_id)
        )
        db.commit()
        return redirect(url_for("manage_movies"))
    return render_template("edit_movie.html", movie=movie)

#admin reviews

@app.route("/admin/manage_reviews")
@login_required
def manage_reviews():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    reviews = db.execute("""
        SELECT reviews.*, movies.title 
        FROM reviews 
        JOIN movies ON reviews.movie_id = movies.movie_id
    """).fetchall()
    return render_template("manage_reviews.html", reviews=reviews)

@app.route("/admin/delete_review/<int:review_id>")
@login_required
def delete_review(review_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    db.commit()
    return redirect(url_for("manage_reviews"))

# admin users

@app.route("/admin/manage_users")
@login_required
def manage_users():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("manage_users.html", users=users)

@app.route("/admin/edit_user/<user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if request.method == "POST":
        new_user_id = request.form["user_id"]
        is_admin = request.form.get("is_admin", False)
        db.execute(
            "UPDATE users SET user_id = ?, is_admin = ? WHERE user_id = ?",
            (new_user_id, is_admin, user_id)
        )
        db.commit()
        return redirect(url_for("manage_users"))
    return render_template("edit_user.html", user=user)

@app.route("/admin/delete_user/<user_id>")
@login_required
def delete_user(user_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    db.commit()
    return redirect(url_for("manage_users"))

# adding stuff

# network

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
