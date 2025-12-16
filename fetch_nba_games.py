from nba_api.stats.endpoints import LeagueGameFinder
import sqlite3

DB_NAME = "nba.db"
MAX_GAMES_PER_RUN = 25

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Create games table 
cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id TEXT PRIMARY KEY,
        game_date TEXT,
        home_team_id INTEGER,
        away_team_id INTEGER,
        home_score INTEGER,
        away_score INTEGER
    )
""")

print("Fetching NBA games from NBA API...")

gamefinder = LeagueGameFinder(season_nullable="2024-25")
df = gamefinder.get_data_frames()[0]

inserted = 0
attempted = 0

for game_id, group in df.groupby("GAME_ID"):
    if inserted >= MAX_GAMES_PER_RUN:
        break

    if len(group) != 2:
        continue

    row1, row2 = group.iloc[0], group.iloc[1]

    # Determine home vs away using MATCHUP
    if "@" in row1["MATCHUP"]:
        away_row = row1
        home_row = row2
    else:
        away_row = row2
        home_row = row1

    cur.execute("""
        INSERT OR IGNORE INTO games
        (game_id, game_date, home_team_id, away_team_id, home_score, away_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        game_id,
        home_row["GAME_DATE"],
        int(home_row["TEAM_ID"]),
        int(away_row["TEAM_ID"]),
        int(home_row["PTS"]),
        int(away_row["PTS"])
    ))

    attempted += 1

    # Only count it if it actually inserted
    if cur.rowcount == 1:
        inserted += 1

conn.commit()
conn.close()

print(f"Inserted {inserted} new games.")
