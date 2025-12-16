from nba_api.stats.static import teams
import sqlite3

DB_NAME = "nba.db"
MAX_TEAMS_PER_RUN = 25


# Connect to the database
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Create teams table 
cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY,
        team_name TEXT,
        city TEXT
    )
""")

print("Fetching NBA teams from NBA API...")

team_list = teams.get_teams()

inserted = 0

for team in team_list:
    if inserted >= MAX_TEAMS_PER_RUN:
        break

    cur.execute("""
        INSERT OR IGNORE INTO teams (team_id, team_name, city)
        VALUES (?, ?, ?)
    """, (
        team["id"],
        team["full_name"],
        team["city"]
    ))

    # Only count if it actually inserted
    if cur.rowcount == 1:
        inserted += 1

conn.commit()
conn.close()

print(f"Inserted {inserted} new teams into database.")
