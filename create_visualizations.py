import sqlite3
import math
import matplotlib.pyplot as plt
import numpy as np

DB_NAME = "nba.db"


# DISTANCE FUNCTION

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# DATABASE

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Team ID → full name
cur.execute("SELECT team_id, team_name FROM teams")
team_names = {row[0]: row[1] for row in cur.fetchall()}

# Join games + locations
cur.execute("""
    SELECT
        g.game_date,
        g.home_team_id,
        g.away_team_id,
        g.home_score,
        g.away_score,
        gl.latitude,
        gl.longitude
    FROM games g
    JOIN game_locations gl ON g.game_id = gl.game_id
    ORDER BY g.game_date
""")

rows = cur.fetchall()
conn.close()


# CALCULATIONS 

team_games = {}
team_wins = {}
team_total_games = {}

for game_date, home_id, away_id, home_score, away_score, lat, lon in rows:
    for team_id in [home_id, away_id]:
        if team_id not in team_games:
            team_games[team_id] = []
            team_wins[team_id] = 0
            team_total_games[team_id] = 0

        team_games[team_id].append((game_date, lat, lon))
        team_total_games[team_id] += 1

    if home_score > away_score:
        team_wins[home_id] += 1
    else:
        team_wins[away_id] += 1


# Travel distance

team_travel = {}

for team_id, games in team_games.items():
    if team_id not in team_names:
        continue

    games.sort(key=lambda x: x[0])
    distance = 0

    for i in range(1, len(games)):
        lat1, lon1 = games[i - 1][1], games[i - 1][2]
        lat2, lon2 = games[i][1], games[i][2]
        distance += haversine(lat1, lon1, lat2, lon2)

    team_travel[team_id] = distance


# Win percentage

team_win_pct = {
    t: team_wins[t] / team_total_games[t]
    for t in team_travel
}


# PREP DATA 

data = [
    (team_names[t], team_travel[t], team_win_pct[t])
    for t in team_travel
]

# Sort by travel
data.sort(key=lambda x: x[1])

teams = [d[0] for d in data]
miles = [d[1] for d in data]
win_pct = [d[2] for d in data]


# BAR CHART: TRAVEL 

plt.figure(figsize=(10, 12))
plt.barh(teams, miles, color="steelblue")
plt.xlabel("Total Miles Traveled")
plt.title("NBA Team Travel Distance (Sample of Games)")
plt.tight_layout()
plt.savefig("team_travel_miles.png")
plt.close()


# BAR CHART: WIN % 

data_sorted_win = sorted(data, key=lambda x: x[2])

plt.figure(figsize=(10, 12))
plt.barh(
    [d[0] for d in data_sorted_win],
    [d[2] for d in data_sorted_win],
    color="firebrick"
)
plt.xlabel("Win Percentage")
plt.xlim(0, 1)
plt.title("NBA Team Win Percentage (Sample of Games)")
plt.tight_layout()
plt.savefig("team_win_percentage.png")
plt.close()


# SCATTER PLOT 

x = np.array(miles)
y = np.array(win_pct)

plt.figure(figsize=(8, 6))

scatter = plt.scatter(
    x,
    y,
    c=y,
    cmap="viridis",
    s=90,
    alpha=0.85
)

# Trend line
m, b = np.polyfit(x, y, 1)
plt.plot(x, m * x + b, linestyle="--", color="black")

plt.xlabel("Total Miles Traveled")
plt.ylabel("Win Percentage")
plt.title("Relationship Between Travel Distance and Win Percentage")

cbar = plt.colorbar(scatter)
cbar.set_label("Win Percentage")

plt.tight_layout()
plt.savefig("travel_vs_win_pct.png")
plt.close()


# CONFERENCE COMPARISON 

east = {
    "Boston Celtics", "Brooklyn Nets", "New York Knicks", "Philadelphia 76ers",
    "Toronto Raptors", "Chicago Bulls", "Cleveland Cavaliers", "Detroit Pistons",
    "Indiana Pacers", "Milwaukee Bucks", "Atlanta Hawks", "Charlotte Hornets",
    "Miami Heat", "Orlando Magic", "Washington Wizards"
}

west = {
    "Dallas Mavericks", "Denver Nuggets", "Golden State Warriors",
    "Houston Rockets", "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
    "Minnesota Timberwolves", "New Orleans Pelicans", "Oklahoma City Thunder",
    "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings",
    "San Antonio Spurs", "Utah Jazz"
}

east_miles = []
west_miles = []

for team_name, miles_traveled, _ in data:
    if team_name in east:
        east_miles.append(miles_traveled)
    elif team_name in west:
        west_miles.append(miles_traveled)

avg_east = sum(east_miles) / len(east_miles)
avg_west = sum(west_miles) / len(west_miles)

plt.figure(figsize=(6, 4))

bars = plt.bar(
    ["Eastern Conference", "Western Conference"],
    [avg_east, avg_west],
    color=["royalblue", "darkred"]
)


plt.ylabel("Average Miles Traveled")
plt.title("Average Team Travel by Conference")
plt.tight_layout()

# Add value labels
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.0f}",
        ha="center",
        va="bottom"
    )

plt.savefig("conference_travel_comparison.png")
plt.close()


print("Visualizations created successfully.")
