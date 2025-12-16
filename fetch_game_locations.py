import sqlite3
import requests
import time

DB_NAME = "nba.db"
MAX_LOCATIONS_PER_RUN = 25
USER_AGENT = "SI201-NBA-Travel-Project"


# Connect to database
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Create table for geocoded game locations
cur.execute("""
    CREATE TABLE IF NOT EXISTS game_locations (
        game_id TEXT PRIMARY KEY,
        team_id INTEGER,
        city TEXT,
        latitude REAL,
        longitude REAL
    )
""")

print("Geocoding game locations using OpenStreetMap...")

# Select games that do not yet have locations
cur.execute("""
    SELECT g.game_id, g.home_team_id, t.city
    FROM games g
    JOIN teams t ON g.home_team_id = t.team_id
    LEFT JOIN game_locations gl ON g.game_id = gl.game_id
    WHERE gl.game_id IS NULL
    LIMIT ?
""", (MAX_LOCATIONS_PER_RUN,))

games_to_geocode = cur.fetchall()

inserted = 0

for game_id, team_id, city in games_to_geocode:
    # Build geocoding request
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params=params,
        headers=headers
    )

    if response.status_code != 200:
        continue

    data = response.json()
    if not data:
        continue

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    cur.execute("""
        INSERT OR IGNORE INTO game_locations
        (game_id, team_id, city, latitude, longitude)
        VALUES (?, ?, ?, ?, ?)
    """, (game_id, team_id, city, lat, lon))

    if cur.rowcount == 1:
        inserted += 1

time.sleep(1)

conn.commit()
conn.close()

print(f"Inserted {inserted} new game locations.")
