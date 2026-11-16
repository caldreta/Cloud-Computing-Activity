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