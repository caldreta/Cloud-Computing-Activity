"""
    from favorites import router as favorites_router      # top
    app.include_router(favorites_router)                  # very bottom
"""
from collections import Counter
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text

from database import engine
from security import get_current_user

router = APIRouter(tags=["Users"])


class CharacterHits(BaseModel):
    # One finished game sends the champions the player got right (a game has at most 10 rounds,
    # matching boards have at most 16 cards), so 20 is a safe cap.
    character_ids: List[int] = Field(min_length=1, max_length=20)


def _user_id(user) -> int:
    value = getattr(user, "id", None)
    return value if value is not None else user["id"]


TOP_QUERY = """
    select c.id, c.name, c.title, c.image, g.name as game,
           s.times_correct, s.last_correct_at
    from user_character_stats s
    join characters c on c.id = s.character_id
    join games g      on g.id = c.game_id
    where s.user_id = :user_id
    order by s.times_correct desc, s.last_correct_at desc, c.name
    limit :limit
"""


def _top(conn, user_id: int, limit: int) -> list:
    rows = conn.execute(text(TOP_QUERY), {"user_id": user_id, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.post("/api/v1/users/me/characters")
def record_correct_characters(body: CharacterHits, user=Depends(get_current_user)):
    """Called by the website after a finished game: +1 for every champion answered correctly."""
    user_id = _user_id(user)
    counts = Counter(body.character_ids)

    with engine.begin() as conn:
        found = conn.execute(
            text("select id from characters where id in :ids").bindparams(bindparam("ids", expanding=True)),
            {"ids": list(counts)},
        ).scalars().all()
        missing = set(counts) - set(found)
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown character id: {sorted(missing)[0]}.")

        for character_id, times in counts.items():
            conn.execute(
                text("""
                    insert into user_character_stats (user_id, character_id, times_correct)
                    values (:user_id, :character_id, :times)
                    on conflict (user_id, character_id) do update
                    set times_correct   = user_character_stats.times_correct + excluded.times_correct,
                        last_correct_at = now()
                """),
                {"user_id": user_id, "character_id": character_id, "times": times},
            )
        top = _top(conn, user_id, 1)

    return {"recorded": sum(counts.values()), "favorite": top[0] if top else None}


@router.get("/api/v1/users/me/characters")
def read_my_top_characters(
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(get_current_user),
):
    """The player's most-guessed champions. The first one is their favorite counter."""
    with engine.begin() as conn:
        top = _top(conn, _user_id(user), limit)
    return {"favorite": top[0] if top else None, "characters": top}
