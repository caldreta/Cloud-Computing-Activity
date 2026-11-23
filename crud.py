from sqlalchemy import text

CHARACTER_SELECT = """
    select c.*, g.name as game
    from characters c
    join games g on g.id = c.game_id
"""


def _like(value: str) -> str:
    #Turn user text into a safe ILIKE pattern (escapes % and _).
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_characters(conn, game=None, role=None):
    sql = CHARACTER_SELECT
    clauses, params = [], {}
    if game:
        clauses.append("lower(g.name) = lower(:game)")
        params["game"] = game
    if role:
        clauses.append("c.role ilike :role escape '\\'")
        params["role"] = _like(role)
    if clauses:
        sql += " where " + " and ".join(clauses)
    sql += " order by c.id"
    return [dict(r) for r in conn.execute(text(sql), params).mappings()]


def get_character(conn, character_id: int):
    row = conn.execute(
        text(CHARACTER_SELECT + " where c.id = :id"), {"id": character_id}
    ).mappings().first()
    return dict(row) if row else None


def search_characters(conn, q: str, game=None):
    clauses = [
        "concat_ws(' ', c.name, c.title, c.region, c.faction, c.role, "
        "c.attack_type, c.origin, cast(c.year_released as text)) ilike :q escape '\\'"
    ]
    params = {"q": _like(q)}
    if game:
        clauses.append("lower(g.name) = lower(:game)")
        params["game"] = game
    sql = CHARACTER_SELECT + " where " + " and ".join(clauses) + " order by c.id"
    return [dict(r) for r in conn.execute(text(sql), params).mappings()]

# ---------- Users ----------

def create_user(conn, username: str, password_hash: str):
    row = conn.execute(
        text(
            "insert into users (username, password_hash) "
            "values (:username, :password_hash) "
            "returning id, username"
        ),
        {"username": username, "password_hash": password_hash},
    ).mappings().one()
    return dict(row)


def get_user_by_username(conn, username: str):
    row = conn.execute(
        text(
            "select id, username, password_hash, is_active "
            "from users where lower(username) = lower(:username)"
        ),
        {"username": username},
    ).mappings().first()
    return dict(row) if row else None


def get_user_by_id(conn, user_id: int):
    row = conn.execute(
        text("select id, username, is_active from users where id = :id"),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else None

# ---------- Progress ----------

def get_game_mode_id(conn, slug: str):
    return conn.execute(
        text("select id from game_modes where slug = :slug"), {"slug": slug}
    ).scalar()


def add_progress(conn, user_id: int, game_mode_id: int, gain: int) -> int:
    # Creates the row on first completion, adds exp afterward, in one statement
    return conn.execute(
        text(
            "insert into user_progress (user_id, game_mode_id, exp) "
            "values (:user_id, :mode_id, :gain) "
            "on conflict (user_id, game_mode_id) "
            "do update set exp = user_progress.exp + excluded.exp "
            "returning exp"
        ),
        {"user_id": user_id, "mode_id": game_mode_id, "gain": gain},
    ).scalar_one()


def list_progress(conn, user_id: int):
    # Every game mode, with 0 exp for modes the user has not played yet
    rows = conn.execute(
        text(
            "select gm.slug, gm.name, gm.category, coalesce(up.exp, 0) as exp "
            "from game_modes gm "
            "left join user_progress up "
            "  on up.game_mode_id = gm.id and up.user_id = :user_id "
            "order by gm.id"
        ),
        {"user_id": user_id},
    ).mappings()
    return [dict(r) for r in rows]

# ---------- Delete ----------

def delete_user(conn, user_id: int) -> int:
    # user_progress rows are removed by ON DELETE CASCADE
    result = conn.execute(text("delete from users where id = :id"), {"id": user_id})
    return result.rowcount

# ---------- Ranks and leaderboard ----------
# Both read the "leaderboard" view and the "ranks" table (see ranks_and_leaderboard.sql).

def list_ranks(conn):
    rows = conn.execute(
        text("select name, min_level, image from ranks order by min_level")
    ).mappings()
    return [dict(r) for r in rows]


# rank_name and rank_image come from the ranks table through users.rank_id
LEADERBOARD_COLUMNS = (
    "place as position, username, total_exp, level, "
    "rank_name as rank, rank_image, next_rank_name as next_rank, next_rank_level"
)


def list_leaderboard(conn, limit: int):
    # Players with no EXP yet are left off the board
    rows = conn.execute(
        text(
            f"select {LEADERBOARD_COLUMNS} from leaderboard "
            "where total_exp > 0 order by place, username limit :limit"
        ),
        {"limit": limit},
    ).mappings()
    return [dict(r) for r in rows]


def count_ranked_players(conn) -> int:
    return conn.execute(
        text("select count(*) from leaderboard where total_exp > 0")
    ).scalar_one()


def get_standing(conn, user_id: int):
    row = conn.execute(
        text(f"select {LEADERBOARD_COLUMNS} from leaderboard where user_id = :id"),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else None
