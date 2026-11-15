from sqlalchemy import text
from database import engine
from seed_data import characters

COLUMNS = [
    "name", "title", "region", "race", "faction", "origin", "personality",
    "relationships", "enemies", "allies", "major_events", "current_status",
    "lore", "image", "role", "weapon", "difficulty", "skill_floor",
    "skill_ceiling", "playstyle", "mobility", "survivability",
    "mechanical_demand", "kit_complexity", "power_curve",
    "snowball_dependence", "team_dependence", "attack_type", "damage_type",
    "damage_source", "year_released",
]
IMAGE_FIXES = {}  # no filename fixes: "jihn.jpg" is kept on purpose


def to_row(character, game_id):
    row = {col: character.get(col) for col in COLUMNS}
    if row["image"]:
        fixed = IMAGE_FIXES.get(row["image"], row["image"])
        row["image"] = f"league/{fixed}"  # namespace by game
    row["game_id"] = game_id
    return row


cols = ["game_id"] + COLUMNS
insert_sql = text(
    f"insert into characters ({', '.join(cols)}) "
    f"values ({', '.join(':' + c for c in cols)})"
)

with engine.begin() as conn:
    existing = conn.execute(text("select count(*) from characters")).scalar()
    if existing:
        raise SystemExit(f"characters already has {existing} rows; refusing to seed twice")
    game_id = conn.execute(
        text("select id from games where name = :n"), {"n": "League of Legends"}
    ).scalar_one()
    rows = [to_row(c, game_id) for c in sorted(characters, key=lambda c: c["id"])]
    conn.execute(insert_sql, rows)
    print("Inserted", len(rows), "characters")