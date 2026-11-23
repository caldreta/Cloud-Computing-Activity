from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import engine
from schemas import CharacterCreate, describe_form
from security import get_current_user, hash_password

router = APIRouter()

EXP_PER_LEVEL = 100  # same value as rules.py


# ---------------------------------------------------------------------------
# Request bodies (same username and password rules as RegisterRequest)
# ---------------------------------------------------------------------------
Username = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
Password = Field(min_length=8, max_length=128)


class AdminCreateUser(BaseModel):
    username: str = Username
    password: str = Password
    role: Literal["user", "admin"] = "user"


class AdminUpdateUser(BaseModel):
    role: Optional[Literal["user", "admin"]] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_change(self):
        if self.role is None and self.is_active is None:
            raise ValueError("Send role, is_active, or both.")
        return self


class AdminSetPassword(BaseModel):
    new_password: str = Password


# ---------------------------------------------------------------------------
# Who is calling?
# ---------------------------------------------------------------------------
def _user_id(user) -> int:
    """get_current_user may return a dict, a row mapping or an object; read the id from any of them."""
    value = getattr(user, "id", None)
    return value if value is not None else user["id"]


def _load_role(user_id: int) -> Optional[str]:
    with engine.begin() as conn:
        return conn.execute(
            text("select role from users where id = :id"), {"id": user_id}
        ).scalar_one_or_none()


def get_current_admin(user=Depends(get_current_user)) -> int:
    """Allows the request only for an active admin. Returns the admin's user id.

    The role is read from the database on every request (not stored in the token),
    so promoting or demoting someone takes effect immediately.
    """
    user_id = _user_id(user)
    if _load_role(user_id) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only.")
    return user_id


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
USER_SUMMARY = """
    select u.id, u.username, u.role, u.is_active,
           coalesce(sum(p.exp), 0)::int as total_exp
    from users u
    left join user_progress p on p.user_id = u.id
"""


def _summary(row) -> dict:
    user = dict(row)
    user["level"] = 1 + user["total_exp"] // EXP_PER_LEVEL
    return user


def _get_user(conn, user_id: int) -> dict:
    row = conn.execute(
        text(USER_SUMMARY + " where u.id = :id group by u.id"), {"id": user_id}
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return _summary(row)


def _active_admin_count(conn) -> int:
    return conn.execute(
        text("select count(*) from users where role = 'admin' and is_active")
    ).scalar_one()


def _guard_own_account(admin_id: int, target_id: int, action: str):
    if admin_id == target_id:
        raise HTTPException(
            status_code=400,
            detail=f"You can't {action} your own account here.",
        )


def _guard_last_admin(conn, target: dict, removes_admin_power: bool):
    if removes_admin_power and target["role"] == "admin" and target["is_active"]:
        if _active_admin_count(conn) <= 1:
            raise HTTPException(status_code=409, detail="There must be at least one active admin.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/api/v1/users/me/role", tags=["Users"])
def read_my_role(user=Depends(get_current_user)):
    """Any logged-in user: tells the website whether to show the admin panel."""
    return {"role": _load_role(_user_id(user))}


@router.get("/api/v1/admin/users", tags=["Admin"])
def admin_list_users(
    search: Optional[str] = Query(default=None, max_length=50),
    admin_id: int = Depends(get_current_admin),
):
    sql = USER_SUMMARY
    params = {}
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " where u.username ilike :pattern escape '\\'"
        params["pattern"] = f"%{escaped}%"
    sql += " group by u.id order by lower(u.username)"
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    users = [_summary(r) for r in rows]
    return {"count": len(users), "users": users}


@router.get("/api/v1/admin/users/{user_id}", tags=["Admin"])
def admin_get_user(user_id: int, admin_id: int = Depends(get_current_admin)):
    with engine.begin() as conn:
        user = _get_user(conn, user_id)
        rows = conn.execute(
            text("""
                select gm.slug, coalesce(p.exp, 0) as exp
                from game_modes gm
                left join user_progress p
                  on p.game_mode_id = gm.id and p.user_id = :id
                order by gm.id
            """),
            {"id": user_id},
        ).mappings().all()
    user["progress"] = [
        {"slug": r["slug"], "exp": r["exp"], "level": 1 + r["exp"] // EXP_PER_LEVEL} for r in rows
    ]
    return user


@router.post("/api/v1/admin/users", status_code=201, tags=["Admin"])
def admin_create_user(body: AdminCreateUser, admin_id: int = Depends(get_current_admin)):
    try:
        with engine.begin() as conn:
            new_id = conn.execute(
                text("""
                    insert into users (username, password_hash, is_active, role)
                    values (:username, :password_hash, true, :role)
                    returning id
                """),
                {
                    "username": body.username,
                    "password_hash": hash_password(body.password),
                    "role": body.role,
                },
            ).scalar_one()
            return _get_user(conn, new_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Username is already taken.")


@router.patch("/api/v1/admin/users/{user_id}", tags=["Admin"])
def admin_update_user(user_id: int, body: AdminUpdateUser, admin_id: int = Depends(get_current_admin)):
    with engine.begin() as conn:
        target = _get_user(conn, user_id)
        demoting = body.role == "user"
        deactivating = body.is_active is False
        if demoting:
            _guard_own_account(admin_id, user_id, "remove admin access from")
        if deactivating:
            _guard_own_account(admin_id, user_id, "deactivate")
        _guard_last_admin(conn, target, demoting or deactivating)

        conn.execute(
            text("""
                update users
                set role = coalesce(:role, role),
                    is_active = coalesce(:is_active, is_active)
                where id = :id
            """),
            {"role": body.role, "is_active": body.is_active, "id": user_id},
        )
        return _get_user(conn, user_id)


@router.patch("/api/v1/admin/users/{user_id}/password", tags=["Admin"])
def admin_set_password(user_id: int, body: AdminSetPassword, admin_id: int = Depends(get_current_admin)):
    with engine.begin() as conn:
        user = _get_user(conn, user_id)
        conn.execute(
            text("update users set password_hash = :hash where id = :id"),
            {"hash": hash_password(body.new_password), "id": user_id},
        )
    return {"detail": f"Password updated for {user['username']}."}


@router.delete("/api/v1/admin/users/{user_id}", status_code=204, tags=["Admin"])
def admin_delete_user(user_id: int, admin_id: int = Depends(get_current_admin)):
    _guard_own_account(admin_id, user_id, "delete")
    with engine.begin() as conn:
        target = _get_user(conn, user_id)
        _guard_last_admin(conn, target, removes_admin_power=True)
        # user_progress rows are removed by the foreign key's ON DELETE CASCADE
        conn.execute(text("delete from users where id = :id"), {"id": user_id})
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Characters: add a champion from the website
# ---------------------------------------------------------------------------
@router.get("/api/v1/admin/characters/form", tags=["Admin"])
def admin_character_form(admin_id: int = Depends(get_current_admin)):
    """Everything the website needs to draw the "add a champion" form.

    The fields come from the CharacterCreate schema, so the form always matches it.
    """
    with engine.begin() as conn:
        games = conn.execute(text("select id, name from games order by id")).mappings().all()
    return {"fields": describe_form(), "games": [dict(g) for g in games]}


@router.post("/api/v1/admin/characters", status_code=201, tags=["Admin"])
def admin_create_character(body: CharacterCreate, admin_id: int = Depends(get_current_admin)):
    data = body.model_dump()
    # Column names come from the schema class above, never from the request, and values are bound parameters.
    columns = list(data)
    insert = (
        f"insert into characters ({', '.join(columns)}) "
        f"values ({', '.join(':' + c for c in columns)}) "
        "returning id, name, title, image"
    )
    try:
        with engine.begin() as conn:
            if conn.execute(text("select 1 from games where id = :id"), {"id": body.game_id}).scalar() is None:
                raise HTTPException(status_code=404, detail="That game does not exist.")
            row = conn.execute(text(insert), data).mappings().one()
    except IntegrityError:
        # characters has a unique (game_id, name) constraint
        raise HTTPException(status_code=409, detail=f"{body.name} already exists for that game.")
    return dict(row)
