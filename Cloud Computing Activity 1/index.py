from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Simple Anime Character API",
    description="A beginner-friendly REST API containing information about anime characters.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ANIME CHARACTER DATA
characters = [

    {
        "id": 1,
        "anime": "The Eminence in Shadow",
        "name": "Cid Kageno",
        "year": 2022,
        "moral_alignment": "Chaotic Neutral",
        "description": "A young man who operates from the shadows."
    },

    {
        "id": 2,
        "anime": "Frieren: Beyond Journey's End",
        "name": "Frieren",
        "year": 2023,
        "moral_alignment": "Neutral Good",
        "description": "An elven mage traveling to understand humanity."
    },

    {
        "id": 3,
        "anime": "Bleach",
        "name": "Ichigo Kurosaki",
        "year": 2004,
        "moral_alignment": "Neutral Good",
        "description": "A substitute Soul Reaper who protects others."
    },

    {
        "id": 4,
        "anime": "Chainsaw Man",
        "name": "Makima",
        "year": 2022,
        "moral_alignment": "Lawful Evil",
        "description": "A manipulative Devil seeking control."
    },

    {
        "id": 5,
        "anime": "One-Punch Man",
        "name": "Garou",
        "year": 2015,
        "moral_alignment": "Chaotic Neutral",
        "description": "A martial artist who hunts heroes."
    }

]


# HOME
@app.get("/")
def home():

    return {
        "message": "Welcome to the Simple Anime Character API!",
        "endpoints": [
            "/characters",
            "/characters/{id}",
            "/characters/search"
        ]
    }


# GET ALL CHARACTERS
@app.get("/characters")
def get_characters():

    return {
        "count": len(characters),
        "characters": characters
    }


# SEARCH CHARACTERS
# IMPORTANT: This must come BEFORE /characters/{character_id}
@app.get("/characters/search")
def search_characters(q: str = Query(..., min_length=1)):

    q = q.lower()
    results = []

    for character in characters:

        searchable_text = (
            f"{character['anime']} "
            f"{character['name']} "
            f"{character['year']} "
            f"{character['moral_alignment']}"
        ).lower()

        if q in searchable_text:
            results.append(character)

    return {
        "query": q,
        "count": len(results),
        "results": results
    }


# GET ONE CHARACTER
@app.get("/characters/{character_id}")
def get_character(character_id: int):

    for character in characters:

        if character["id"] == character_id:
            return character

    raise HTTPException(
        status_code=404,
        detail="Character not found."
    )