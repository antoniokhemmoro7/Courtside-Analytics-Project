import sqlite3

DB_NAME = "nba.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Build team_id -> team_name lookup
cur.execute("SELECT team_id, team_name FROM teams")
team_names = {}
for team_id, team_name in cur.fetchall():
    team_names[team_id] = team_name

# Pull all games (home + away) using a JOIN
cur.execute("""
    SELECT
        g.home_team_id,
        g.away_team_id,
        g.home_score,
        g.away_score
    FROM games g
    JOIN teams t ON g.home_team_id = t.team_id
""")

rows = cur.fetchall()
conn.close()

# Track wins and total games per team
team_stats = {}

for home_id, away_id, home_score, away_score in rows:
    # Initialize teams if not seen yet
    if home_id not in team_stats:
        team_stats[home_id] = {"wins": 0, "games": 0}
    if away_id not in team_stats:
        team_stats[away_id] = {"wins": 0, "games": 0}

    # Every game counts once for each team
    team_stats[home_id]["games"] += 1
    team_stats[away_id]["games"] += 1

    # Determine winner
    if home_score > away_score:
        team_stats[home_id]["wins"] += 1
    else:
        team_stats[away_id]["wins"] += 1

# Calculate win percentage
team_win_pct = {}

for team_id in team_stats:
    wins = team_stats[team_id]["wins"]
    games = team_stats[team_id]["games"]
    win_pct = wins / games if games > 0 else 0
    team_win_pct[team_id] = win_pct

# Print results (sorted by win percentage)
sorted_teams = sorted(team_win_pct.items(), key=lambda x: x[1], reverse=True)

# Write results to output file
with open("team_win_percentage_results.txt", "w") as f:
    f.write("Win percentage by team (based on games in DB):\n")
    f.write("--------------------------------------------\n")
    for team_id, win_pct in sorted_teams:
        name = team_names.get(team_id, str(team_id))
        f.write(f"{name}: {win_pct:.3f}\n")

print("team_win_percentage_results.txt created successfully.")
