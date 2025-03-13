from flask import Flask, render_template, session, redirect, url_for, g, request
# import random
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SearchForm,MovieForm, ScoreForm, YearForm, RegistrationForm, LoginForm, ReviewForm, UpdateUsernameForm, MovieSuggestionForm, TicketForm, AdminResponseForm
from functools import wraps
import os

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "jordansPw"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/images" # directory for my images
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg"} # using so only jpgs and pngs can be used
Session(app)

###########
# checkers 
##########

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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    # check to see if the filename is a jpg or png


####################################
# Movie main stuff search routes
####################################

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    query = request.args.get('query', '').strip() # gets the search query strip used for user handling
    filter_type = request.args.get('filter', 'all') # default for search

    db = get_db()
    cur = db.cursor() # creates a cursor for db

    if filter_type == 'genre': # pulls all movies of the specific genre
        if query:
            cur.execute("SELECT * FROM movies WHERE genre LIKE ?", ('%' + query + '%',))
        else:
            cur.execute("SELECT * FROM movies") # gets everything from db if nothing is entered
        results = cur.fetchall()
        return render_template('search.html', results=results)
    elif filter_type == 'score': # filters through minimum scores (why add a max who wants to see sh1t movies)
        try:
            min_score = float(query)
            cur.execute("SELECT * FROM movies WHERE score >= ?", (min_score,))
            results = cur.fetchall()
            return render_template('search.html', results=results)
        except ValueError: # if error happens it shows all movies (done for all)
            cur.execute("SELECT * FROM movies") 
            results = cur.fetchall()
            return render_template('search.html', results=results)
    elif filter_type == 'year': # allows for a year to search by (maybe should be by decade, i like specificity tho)
        try:
            year_value = int(query)
            cur.execute("SELECT * FROM movies WHERE year = ?", (year_value,))
            results = cur.fetchall()
            return render_template('search.html', results=results)
        except ValueError:
            cur.execute("SELECT * FROM movies")
            results = cur.fetchall()
            return render_template('search.html', results=results)
    elif filter_type == 'highest_reviewed': # grabs the 10 highest reviewed movies by users e.g., 10 score
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
    elif filter_type == 'all': # this checks if a title of a movie is input e.g., the matrix
        if query:
            cur.execute("SELECT * FROM movies WHERE title LIKE ?", ('%' + query + '%',))
            results = cur.fetchall()
            return render_template('search.html', results=results)
        else:
            cur.execute("SELECT * FROM movies")
            all_movies = cur.fetchall()

            movies_by_genre = {} # ensures movies are categorised
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
    form = ReviewForm() # used to show the reviews under the movies

    if request.method == "GET":
        movie = db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1").fetchone() # gets 1 random movie at a time
        session["random_movie_id"] = movie["movie_id"]
    else:
        movie_id = session.get("random_movie_id")
        if not movie_id:
            return "Error: No movie ID found in session. Please try again.", 400 # some error handling

        movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone() # ensures that if a review is left it correlates with the right id
        if not movie:
            return "Error: Movie not found. Please try again.", 404

    if form.validate_on_submit():
        review_text = form.review_text.data
        rating = form.rating.data
        user = session.get("user_id")

        movie_id = session.get("random_movie_id")
        if not movie_id:
            return "Error: No movie ID found in session. Please try again.", 400
        # allows review to be added
        db.execute(
            "INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
            (movie_id, user, review_text, rating),
        )
        db.commit()

        return redirect(url_for("random_movie")) # refreshes page for new movie

    # fetches reviews of current movie
    reviews = db.execute("SELECT * FROM reviews WHERE movie_id = ?", (movie["movie_id"],)).fetchall()

    return render_template("random.html", movie=movie, reviews=reviews, form=form)

@app.route("/genre", methods=["GET", "POST"])
@login_required
def genre_search():
    form = MovieForm()
    if form.validate_on_submit():
        genre = form.genre.data
        return redirect(url_for("search", query=genre, filter="genre")) # filters by genre like the search
    
    return render_template("genre.html", form=form)

@app.route("/score", methods=["GET", "POST"])
@login_required
def score_search():
    form = ScoreForm()
    if form.validate_on_submit():
        min_score = form.min_score.data
        return redirect(url_for("search", query=f"{min_score}", filter="score")) # filters by score again like the search
    
    return render_template("score.html", form=form)

@app.route("/year", methods=["GET", "POST"])
@login_required
def year_search():
    form = YearForm()
    if form.validate_on_submit():
        year = form.year.data
        return redirect(url_for("search", query=year, filter="year")) # filters by release date
    
    return render_template("year.html", form=form)

# DNA SECTION
@app.route("/my-dna")
@login_required
def my_dna():
    db = get_db()
    user_id = session["user_id"] # ensures personal to user

    # gets user watchlist 
    watchlist = db.execute("""
        SELECT movies.* 
        FROM watchlist
        JOIN movies ON watchlist.movie_id = movies.movie_id
        WHERE watchlist.user_id = ?
    """, (user_id,)).fetchall()

    watchlist = [dict(movie) for movie in watchlist] # goes through watch list

    user_genres = {movie["genre"] for movie in watchlist} # checks unique genre of movies in watchlist
    user_min_score = min((movie["score"] for movie in watchlist), default=0) # checks their minimum score

    # gets users average reviewed
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

    # combines watchlist and highly reviewed movies, ensuring uniqueness
    unique_movies = {}

    for movie in watchlist:
        unique_movies[movie["movie_id"]] = movie

    for movie in highly_reviewed:
        if movie["movie_id"] not in unique_movies and movie["score"] >= user_min_score:
            unique_movies[movie["movie_id"]] = movie

    recommended_movies = list(unique_movies.values())

    return render_template("my_dna.html", movies=recommended_movies)

##########################
# Session cart/watchlist
##########################

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
    
    # check if already in watchlist 
    existing_watchlist_item = db.execute(
        "SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?",
        (user_id, movie_id)
    ).fetchone()

    # increments counter each time added
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
    return redirect(request.referrer)

@app.route("/clear_watchlist") # wipes all of users watchlist 
@login_required
def clear_watchlist():
    db = get_db()
    user_id = session["user_id"]

    db.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
    db.commit()

    return redirect(url_for("cart"))

##################
# Review section
##################

@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
@login_required
def movie_details(movie_id):
    db = get_db()
    form = ReviewForm()
    
    if form.validate_on_submit():
        # gets the review form
        review_text = form.review_text.data
        rating = form.rating.data
        user = "Anonymous" # defaults to anonymous (worked at the start pointless now)
        db.execute("INSERT INTO reviews (movie_id, user, review_text, rating) VALUES (?, ?, ?, ?)",
                   (movie_id, user, review_text, rating))
        db.commit()
    
    # fetches movie details and reviews
    movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE movie_id = ?", (movie_id,)).fetchall()

    return render_template("reviews.html", movie=movie, 
                           reviews=reviews, 
                           form=form)

###############
# User section 
##############

@app.route('/user', methods=["GET", "POST"])
@login_required
def user():
    db = get_db()
    user_id = session.get("user_id")
    form = UpdateUsernameForm()

    # gets current username
    if form.validate_on_submit():
        new_username = form.username.data

    	# checks if username already exists
        existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
        if existing_user:
            form.username.errors.append("Username already exists. Please choose a different one.")
        else:
            # if its not taken changes username and updates db
            db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", (new_username, user_id))
            db.commit()
        
            # update session with new name
            session["user_id"] = new_username
            session.modified = True

            return redirect(url_for("user"))

    # fetches user reviews
    reviews = db.execute("""
        SELECT reviews.*, movies.title 
        FROM reviews 
        JOIN movies ON reviews.movie_id = movies.movie_id 
        WHERE reviews.user = ?
    """, (user_id,)).fetchall()

    all_users = db.execute("SELECT user_id FROM users").fetchall()

    # gets all network stuff
    followers = db.execute(
        "SELECT follower FROM network WHERE following = ?",
        (user_id,)
    ).fetchall()

    following = db.execute(
        "SELECT following FROM network WHERE follower = ?",
        (user_id,)
    ).fetchall()

    # convert followers and following to sets for easier manipulation
    follower_set = {follower["follower"] for follower in followers}
    following_set = {follow["following"] for follow in following}

    return render_template(
        'user.html',
            form=form,
            reviews=reviews,
            all_users=all_users,
            followers=followers,
            following=following,
            follower_set=follower_set,
            following_set=following_set
    )

@app.route("/edit_username", methods=["POST"])
@login_required
def edit_username():
    new_username = request.form.get("new_username")
    db = get_db()

    # check if the new username already exists
    existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
    if existing_user:
        return "Username already exists. Please choose a different one.", 400

    db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", (new_username, session["user_id"]))
    db.commit()

    session["user_id"] = new_username
    session.modified = True

    return redirect(url_for("index"))

#########################
# Login/register section
#########################

@app.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()

        # check to see if name in db
        user_in_db = db.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,)).fetchone()
        if user_in_db:
            form.user_id.errors.append("User ID already exists! Please choose a different one.")
        else:
            # insert hashed pw into db
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

        # check if the user exists
        user_in_db = db.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,)).fetchone()
        if user_in_db is None:
            form.user_id.errors.append("No such user name!")
        elif not check_password_hash(user_in_db["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            # log the user in
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

######################
# admin login section
######################

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    # only displays if user is the admin
    if not g.is_admin:
        return "Access denied. Admin only.", 403
    return render_template("admin_dashboard.html")

###############
# admin movies
###############

@app.route("/admin/manage_movies")
@login_required
def manage_movies():
    # displays management page
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    db = get_db()
    movies = db.execute("SELECT * FROM movies").fetchall()
    return render_template("manage_movies.html", movies=movies)
@app.route("/admin/add_movie", methods=["GET", "POST"])

@login_required
def add_movie():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    
    form = MovieSuggestionForm()
    
    if form.validate_on_submit():
        image = form.image.data
        if image and allowed_file(image.filename):
            # save the image to directory
            filename = form.title.data.replace(" ", "_") + ".jpg"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename
        else:
            image_path = None
        
        db = get_db()

        # insert new movie into db
        db.execute(
            """
            INSERT INTO movies (title, genre, score, year, director, description, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form.title.data, form.genre.data, form.score.data, form.year.data,
                form.director.data, form.description.data, image_path
            )
        )
        db.commit()
        
        return redirect(url_for("manage_movies"))
    
    return render_template("add_movie.html", form=form)

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
    
    if request.method == "POST":
        # update the movies
        title = request.form.get("title")
        genre = request.form.get("genre")
        score = request.form.get("score")
        year = request.form.get("year")
        director = request.form.get("director")
        description = request.form.get("description")

        # makes sure all fields are entered
        if not title or not genre or not score or not year or not director or not description:
            return "All fields are required.", 400
        
        try: # ensure correct stuff entered
            score = float(score)
            year = int(year)
        except ValueError:
            return "Invalid score or year.", 400
        
        # get details of movie to edit
        db.execute(
            """
            UPDATE movies 
            SET title = ?, genre = ?, score = ?, year = ?, director = ?, description = ? 
            WHERE movie_id = ?
            """,
            (title, genre, score, year, director, description, movie_id)
        )
        db.commit()
        
        return redirect(url_for("manage_movies"))
    
    movie = db.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,)).fetchone()
    
    if not movie:
        return "Movie not found.", 404
    
    return render_template("edit_movie.html", movie=movie)

################
#admin reviews
###############

@app.route("/admin/manage_reviews")
@login_required
def manage_reviews():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    
    db = get_db()
    
    # gets all reviews
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
    
    # deletes selected movie
    db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    db.commit()
    
    return redirect(url_for("manage_reviews"))

##############
# admin users
##############

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
    
    if request.method == "POST":
        # change the username
        new_username = request.form.get("new_username")
        
        if not new_username:
            return "New username is required.", 400
        
        # check if the new username already exists
        existing_user = db.execute("SELECT * FROM users WHERE user_id = ?", (new_username,)).fetchone()
        if existing_user:
            return "Username already exists. Please choose a different one.", 400
        
        # update the username in the database
        db.execute(
            "UPDATE users SET user_id = ? WHERE user_id = ?",
            (new_username, user_id)
        )
        db.commit()
        
        return redirect(url_for("manage_users"))
    
    # get user details to edit
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    if not user:
        return "User not found.", 404
    
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

##################################
# network (follow/unfollow users)
#################################

@app.route("/follow/<username>")
@login_required
def follow_user(username):
    db = get_db()
    current_user = session["user_id"]

    # makes sure user cant follow themselves
    if current_user == username:
        return "You cannot follow yourself.", 400

    # check if the user to follow exists
    user_to_follow = db.execute("SELECT * FROM users WHERE user_id = ?", (username,)).fetchone()
    if not user_to_follow:
        return "User not found.", 404

    # check if already following target user
    existing_follow = db.execute(
        "SELECT * FROM network WHERE follower = ? AND following = ?",
        (current_user, username)
    ).fetchone()

    if existing_follow:
        return "You are already following this user.", 400

    # insert the relationship into the database
    db.execute("INSERT INTO network (follower, following) VALUES (?, ?)", (current_user, username))
    db.commit()

    return redirect(url_for("user", username=username))

@app.route("/unfollow/<username>")
@login_required
def unfollow_user(username):
    db = get_db()
    current_user = session["user_id"]

    # check if the current user is following the target user
    existing_follow = db.execute(
        "SELECT * FROM network WHERE follower = ? AND following = ?",
        (current_user, username)
    ).fetchone()

    if not existing_follow:
        return "You are not following this user.", 400

    db.execute("DELETE FROM network WHERE follower = ? AND following = ?", (current_user, username))
    db.commit()

    return redirect(url_for("user", username=username))

@app.route("/user/<username>")
@login_required
def user_profile(username):
    db = get_db()

    # fetch the current users profile
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (username,)).fetchone()
    if not user:
        return "User not found.", 404

    # get reviews by the user
    reviews = db.execute("""
        SELECT reviews.*, movies.title 
        FROM reviews 
        JOIN movies ON reviews.movie_id = movies.movie_id 
        WHERE reviews.user = ?
    """, (username,)).fetchall()

    # fetc followers and following
    followers = db.execute(
        "SELECT follower FROM network WHERE following = ?",
        (username,)
    ).fetchall()

    following = db.execute(
        "SELECT following FROM network WHERE follower = ?",
        (username,)
    ).fetchall()

    # create a set of users the current user is already following
    following_set = {row["following"] for row in following}

    # check if the current user is following the profile user
    is_following = db.execute(
        "SELECT * FROM network WHERE follower = ? AND following = ?",
        (session["user_id"], username)
    ).fetchone() is not None

    # fetch all users except the current user
    all_users = db.execute("SELECT * FROM users WHERE user_id != ?", (session["user_id"],)).fetchall()

    # filter out users that the current user is already following
    suggested_users = [user for user in all_users if user["user_id"] not in following_set]

    return render_template(
        "user_profile.html",
        user=user,
        reviews=reviews,
        followers=followers,
        following=following,
        is_following=is_following,
        all_users=suggested_users,
        following_set=following_set
)

###################
# user suggestions
###################

@app.route("/suggest_movie", methods=["GET", "POST"])
@login_required
def suggest_movie():
    form = MovieSuggestionForm()
    
    # similar code to the add movie in admin section
    if form.validate_on_submit():
        image = form.image.data
        if image and allowed_file(image.filename):
            # save the image to folder
            filename = form.title.data.replace(" ", "_") + ".jpg"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename
        else:
            image_path = None
        
        db = get_db()
        
        # insert the movie suggestion into the suggestion database only
        db.execute(
            """
            INSERT INTO movie_suggestions (user_id, title, genre, year, director, description, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"], form.title.data, form.genre.data, form.year.data, 
                form.director.data, form.description.data, image_path
            )
        )
        db.commit()
        
        return redirect(url_for("index"))
    
    return render_template("suggest_movie.html", form=form)

##########################
# admin check suggestion
##########################

@app.route("/admin/movie_suggestions")
@login_required
def view_movie_suggestions():
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    
    db = get_db()
    suggestions = db.execute("SELECT * FROM movie_suggestions").fetchall()
    # gets all current suggestions in suggestion db by users
    return render_template("view_suggestions.html", suggestions=suggestions)

@app.route("/admin/accept_suggestion/<int:suggestion_id>")
@login_required
def accept_suggestion(suggestion_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    
    db = get_db()
    
    suggestion = db.execute("SELECT * FROM movie_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    if not suggestion:
        return "Suggestion not found.", 404
    
    # inserts movie into movie db if accepted
    db.execute(
        """
        INSERT INTO movies (title, genre, score, year, director, description, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            suggestion["title"], suggestion["genre"], suggestion["score"], suggestion["year"], 
            suggestion["director"], suggestion["description"], suggestion["image_path"]
        )
    )
    
    # clears it from suggestion db
    db.execute("DELETE FROM movie_suggestions WHERE id = ?", (suggestion_id,))
    
    db.commit()
    
    return redirect(url_for("view_movie_suggestions"))


@app.route("/admin/reject_suggestion/<int:suggestion_id>")
@login_required
def reject_suggestion(suggestion_id):
    if not g.is_admin:
        return "Access denied. Admins only.", 403
    
    db = get_db()
    
    suggestion = db.execute("SELECT * FROM movie_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    if not suggestion:
        return "Suggestion not found.", 404
    
    # if suggested movie rejected deletes it from db (bye bye)
    db.execute("DELETE FROM movie_suggestions WHERE id = ?", (suggestion_id,))
    
    db.commit()
    
    return redirect(url_for("view_movie_suggestions"))

###############
# ticket form
##############

@app.route("/submit_ticket", methods=["GET", "POST"])
def submit_ticket():
    form = TicketForm()

    db = get_db()
    
    if form.validate_on_submit():
        question = form.question.data
        user_id = session.get('user_id') 
        
        # adds the ticket to be answered by admin
        db.execute("INSERT INTO tickets (user_id, question) VALUES (?, ?)", (user_id, question))
        db.commit()
        
        return redirect(url_for("submit_ticket"))
    
    # gets all tickets so users can see 
    tickets = db.execute("SELECT * FROM tickets").fetchall()

    return render_template("submit_ticket.html", form=form, tickets=tickets)

########################
# admin ticket response
#######################

@app.route("/admin_tickets", methods=["GET", "POST"])
def admin_tickets():
    db = get_db()
    
    # gets only the tickets that have not been responded to
    tickets = db.execute("SELECT * FROM tickets WHERE is_responded = 0").fetchall()

    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        response = request.form.get("response")
        
        # update ticket with admin response
        if ticket_id and response:
            db.execute("UPDATE tickets SET response = ?, is_responded = 1 WHERE id = ?", (response, ticket_id))
            db.commit()
            
            return redirect(url_for("admin_tickets"))
    
    return render_template("admin_tickets.html", tickets=tickets)

######################
# page for references
######################

@app.route("/references", methods=["GET","POST"])
def references():
    return render_template("references.html")

# @app.errorhandler(404)
# def page_not_found(e):
#     return "<h1>404</h1><p>The resource could not be found. Please check if there was an error with how the link was typed up.</p>"

# @app.errorhandler(405)
# def handle_exception(e):
#     return "<h1>405 Method not Allowed</h1><p>The server has received the request but rejected the specific HTTP method used please try again</p>"

# @app.errorhandler(500)
# def handle_exception(e):
#     return "<h1>500 Internal Server Error</h1><p>The server encountered an unexpected condition that prevented it from fulfilling the request</p>"

# @app.errorhandler(403)
# def handle_exception(e):
#     return "<h1>403 Forbidden</h1><p>The request you have made is forbidden</p>"

# if __name__ == "__main__":
#     app.run(debug=True)
