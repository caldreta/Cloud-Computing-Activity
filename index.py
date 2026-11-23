import logging
from admin import router as admin_router
from favorites import router as favorites_router
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from config import ALLOWED_ORIGINS
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import crud
from database import get_conn
from schemas import LoginRequest, ProgressUpdate, RegisterRequest
from rules import exp_gain, level_for
from security import (
    TOKEN_MINUTES,
    create_access_token,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_api_key,
    verify_password,
)

logger = logging.getLogger("api")

app = FastAPI(
    title="MOBA Character and Game Hub API",
    description="Character data and player progress, backed by Supabase PostgreSQL.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# ---------- Error handlers ----------

@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: OperationalError):
    # Log the type only, so no connection details reach the logs or the client
    logger.error("Database unavailable: %s", type(exc).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is temporarily unavailable. Please try again later."},
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    logger.error("Database operation failed: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception("Unexpected error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/")
def home():
    return {
        "message": "Welcome to the MOBA Character and Game Hub API!",
        "endpoints": [
            "/api/v1/characters",
            "/api/v1/characters/search?q=",
            "/api/v1/characters/{id}",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/users/me",
            "/api/v1/ranks",
            "/api/v1/leaderboard",
        ],
    }


@app.get("/health")
def health_check(conn=Depends(get_conn)):
    conn.execute(text("select 1"))
    return {
        "status": "ok",
        "database": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------- Characters (API key) ----------

@app.get("/api/v1/characters", dependencies=[Depends(verify_api_key)])
def get_characters(
    game: str | None = Query(None),
    role: str | None = Query(None),
    conn=Depends(get_conn),
):
    result = crud.list_characters(conn, game=game, role=role)
    return {"count": len(result), "characters": result}


# Declared before /{character_id} so "search" is not read as an id
@app.get("/api/v1/characters/search", dependencies=[Depends(verify_api_key)])
def search_characters(
    q: str = Query(..., min_length=1, max_length=100),
    game: str | None = Query(None),
    conn=Depends(get_conn),
):
    results = crud.search_characters(conn, q, game=game)
    return {"query": q, "count": len(results), "results": results}


@app.get("/api/v1/characters/{character_id}", dependencies=[Depends(verify_api_key)])
def get_character(character_id: int, conn=Depends(get_conn)):
    character = crud.get_character(conn, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found.")
    return character


# ---------- Accounts (public) ----------

@app.post("/api/v1/auth/register", status_code=201)
def register(body: RegisterRequest, conn=Depends(get_conn)):
    try:
        user = crud.create_user(conn, body.username, hash_password(body.password))
    except IntegrityError:
        # The unique index on lower(username) rejected a duplicate
        raise HTTPException(status_code=409, detail="Username is already taken.")
    return user


@app.post("/api/v1/auth/login")
def login(body: LoginRequest, conn=Depends(get_conn)):
    user = crud.get_user_by_username(conn, body.username)
    valid = verify_password(user["password_hash"] if user else None, body.password)
    if not valid or not user["is_active"]:
        # Same message for unknown user and wrong password
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {
        "access_token": create_access_token(user["id"]),
        "token_type": "bearer",
        "expires_in": TOKEN_MINUTES * 60,
    }


# ---------- Ranks and leaderboard (public) ----------

@app.get("/api/v1/ranks")
def get_ranks(conn=Depends(get_conn)):
    return {"ranks": crud.list_ranks(conn)}


@app.get("/api/v1/leaderboard")
def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_optional_user),
    conn=Depends(get_conn),
):
    # "me" is only filled in when a valid login token is sent
    return {
        "total_players": crud.count_ranked_players(conn),
        "leaders": crud.list_leaderboard(conn, limit),
        "me": crud.get_standing(conn, user["id"]) if user else None,
    }


# ---------- Current user (token) ----------

@app.get("/api/v1/users/me")
def read_me(user=Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"]}

@app.get("/api/v1/users/me/progress")
def read_my_progress(user=Depends(get_current_user), conn=Depends(get_conn)):
    rows = crud.list_progress(conn, user["id"])
    return {
        "username": user["username"],
        "progress": [{**r, "level": level_for(r["exp"])} for r in rows],
        # overall level and rank, stored by the database
        "standing": crud.get_standing(conn, user["id"]),
    }


# :path allows slugs that contain a slash, such as loldle/classic
@app.patch("/api/v1/users/me/progress/{mode_slug:path}")
def update_my_progress(
    mode_slug: str,
    body: ProgressUpdate,
    user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    mode_id = crud.get_game_mode_id(conn, mode_slug)
    if mode_id is None:
        raise HTTPException(status_code=404, detail="Game mode not found.")
    gain = exp_gain(body.correct_answers)
    total = crud.add_progress(conn, user["id"], mode_id, gain)
    return {
        "game_mode": mode_slug,
        "exp_gained": gain,
        "exp": total,
        "level": level_for(total),
        # the database trigger has already updated the player's rank
        "standing": crud.get_standing(conn, user["id"]),
    }

@app.delete("/api/v1/users/me", status_code=204)
def delete_my_account(user=Depends(get_current_user), conn=Depends(get_conn)):
    crud.delete_user(conn, user["id"])
    return Response(status_code=204)

app.include_router(admin_router)
app.include_router(favorites_router) 
