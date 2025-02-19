-- database information found from the internet IMDB

DROP TABLE IF EXISTS movies;

CREATE TABLE movies 
(
    movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    score FLOAT,
    year INTEGER,
    director TEXT,
    description TEXT
);

INSERT INTO movies (title, genre, score, year, director, description) VALUES
    ('Inception', 'Sci-Fi', 8.8, 2010, 'Christopher Nolan', 'A thief who steals corporate secrets through the use of dream-sharing technology.'),
    ('The Dark Knight', 'Action', 9.0, 2008, 'Christopher Nolan', 'When the menace known as the Joker emerges, Batman must confront chaos.'),
    ('Interstellar', 'Sci-Fi', 8.6, 2014, 'Christopher Nolan', 'A team of explorers travel through a wormhole in space in an attempt to ensure humanitys survival.'),
    ('The Matrix', 'Sci-Fi', 8.7, 1999, 'Lana Wachowski', 'A computer hacker learns about the true nature of reality and his role in the war against its controllers.'),
    ('Pulp Fiction', 'Crime', 8.9, 1994, 'Quentin Tarantino', 'The lives of two mob hitmen, a boxer, and a pair of diner bandits intertwine in four tales of violence and redemption.'),
    ('The Shawshank Redemption', 'Drama', 9.3, 1994, 'Frank Darabont', 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.'),
    ('Fight Club', 'Drama', 8.8, 1999, 'David Fincher', 'An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much, much more.'),
    ('Forrest Gump', 'Drama', 8.8, 1994, 'Robert Zemeckis', 'The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate, and other historical events unfold through the perspective of an Alabama man with an IQ of 75.'),
    ('The Lord of the Rings: The Return of the King', 'Fantasy', 8.9, 2003, 'Peter Jackson', 'Gandalf and Aragorn lead the World of Men against Saurons army to draw his gaze from Frodo and Sam as they approach Mount Doom with the One Ring.'),
    ('Gladiator', 'Action', 8.5, 2000, 'Ridley Scott', 'A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.');