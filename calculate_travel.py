import sqlite3
import math

DB_NAME = "nba.db"


# Distance in miles between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Build a mapping from team_id -> team_name (for printing)
cur.execute("SELECT team_id, team_name FROM teams")
team_name_lookup = {}
for team_id, team_name in cur.fetchall():
    team_name_lookup[team_id] = team_name

# Pull EVERY game from DB and attach location to it:
# location = home team city coords (where the game was played)
cur.execute("""
    SELECT
        g.game_date,
        g.home_team_id,
        g.away_team_id,
        gl.latitude,
        gl.longitude
    FROM games g
    JOIN game_locations gl ON g.game_id = gl.game_id
    ORDER BY g.game_date
""")

rows = cur.fetchall()
conn.close()

# Build per-team game sequence (home + away)
team_games = {}

for game_date, home_id, away_id, lat, lon in rows:
    # This location applies to BOTH teams (they both played here)
    if home_id not in team_games:
        team_games[home_id] = []
    if away_id not in team_games:
        team_games[away_id] = []

    team_games[home_id].append((game_date, lat, lon))
    team_games[away_id].append((game_date, lat, lon))

# Sort each team's games by date 
for team_id in team_games:
    team_games[team_id].sort(key=lambda x: x[0])

# Calculate travel distance per team
team_travel = {}

for team_id, games in team_games.items():
    total = 0.0

    for i in range(1, len(games)):
        lat1, lon1 = games[i - 1][1], games[i - 1][2]
        lat2, lon2 = games[i][1], games[i][2]

        total += haversine(lat1, lon1, lat2, lon2)

    team_travel[team_id] = total

# Sort teams by total travel distance (descending)
sorted_teams = sorted(team_travel.items(), key=lambda x: x[1], reverse=True)

# Write results to output file 
with open("team_travel_results.txt", "w") as f:
    f.write("Travel distance by team (based on games in your DB):\n")
    f.write("--------------------------------------------------\n")
    for team_id, miles in sorted_teams:
        name = team_name_lookup.get(team_id, str(team_id))
        f.write(f"{name}: {miles:.2f} miles\n")

print("team_travel_results.txt created successfully.")
