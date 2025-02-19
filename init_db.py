import sqlite3

# Connect to the database
conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Read the schema from the file
with open("schema.sql", "r") as f:
    schema = f.read()

# Execute schema SQL commands
cur.executescript(schema)

# Commit and close
conn.commit()
conn.close()
