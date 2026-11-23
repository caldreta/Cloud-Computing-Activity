from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    # Letters, numbers and underscores only, 3 to 50 characters
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)

class ProgressUpdate(BaseModel):
    correct_answers: int = Field(ge=0, le=100)
    total_questions: int = Field(ge=1, le=100)

    @model_validator(mode="after")
    def correct_not_above_total(self):
        if self.correct_answers > self.total_questions:
            raise ValueError("correct_answers cannot be greater than total_questions")
        return self

# ---------------------------------------------------------------------------
# Characters (admin: add a champion)
# One field per column of the characters table, except id, which the database
# generates. The allowed values and limits copy the table's CHECK constraints,
# so a bad value is refused here with a clear message instead of by the database.
# The admin form on the website is built from this class (see describe_form),
# so adding or changing a field here changes the form too.
# ---------------------------------------------------------------------------
from typing import Literal, Optional, get_args, get_origin

from pydantic import ConfigDict


def _text(label, group, hint=None, example=None, textarea=False, max_length=2000):
    extra = {"label": label, "group": group}
    if hint:
        extra["hint"] = hint
    if example:
        extra["example"] = example
    if textarea:
        extra["textarea"] = True
    return Field(min_length=1, max_length=max_length, json_schema_extra=extra)


def _choice(label, hint=None):
    extra = {"label": label, "group": "Gameplay"}
    if hint:
        extra["hint"] = hint
    return Field(json_schema_extra=extra)


class CharacterCreate(BaseModel):
    # Leading and trailing spaces are removed before anything is checked
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # ----- Identity -----
    game_id: int = Field(ge=1, json_schema_extra={"label": "Game", "group": "Identity", "widget": "game"})
    name: str = _text("Name", "Identity", example="Zed", max_length=100)
    title: str = _text("Title", "Identity", example="The Master of Shadows", max_length=150)
    image: Optional[str] = Field(
        default=None, max_length=200, pattern=r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-]+)*\.(jpg|jpeg|png|webp)$",
        json_schema_extra={
            "label": "Image file", "group": "Identity", "example": "league/zed.jpg",
            "hint": "Path inside the website's images folder. Add the file to that folder too. Optional.",
        },
    )
    year_released: int = Field(
        ge=1998, le=2150, json_schema_extra={"label": "Year released", "group": "Identity", "example": "2012"}
    )
    region: str = _text("Region", "Identity", hint="Separate several with ' / ', like Piltover / Zaun.", example="Ionia", max_length=100)
    race: str = _text("Race", "Identity", example="Human", max_length=100)
    faction: str = _text("Faction", "Identity", example="Order of Shadow", max_length=150)
    origin: str = _text("Origin", "Identity", example="Ionia", max_length=150)
    weapon: str = _text("Weapon", "Identity", example="Living Shadows", max_length=150)

    # ----- Story -----
    personality: str = _text("Personality", "Story", textarea=True)
    relationships: str = _text("Relationships", "Story", textarea=True)
    enemies: str = _text("Enemies", "Story", textarea=True)
    allies: str = _text("Allies", "Story", textarea=True)
    major_events: str = _text("Major events", "Story", textarea=True)
    current_status: str = _text("Current status", "Story", textarea=True)
    lore: Optional[str] = Field(
        default=None, min_length=1, max_length=8000,
        json_schema_extra={"label": "Lore", "group": "Story", "textarea": True,
                           "hint": "The story paragraph the Lore games use. Optional."},
    )

    # ----- Gameplay -----
    role: str = _text("Role", "Gameplay", hint="Separate several with ' / ', like Fighter / Assassin.", example="Assassin", max_length=100)
    playstyle: Literal["Burst", "Sustained", "Poke", "Frontline", "Ambush", "Utility"] = _choice("Playstyle")
    mobility: Literal["Low", "Medium", "High"] = _choice("Mobility")
    survivability: Literal["Squishy", "Sturdy", "Sustain-heavy"] = _choice("Survivability")
    mechanical_demand: Literal["Aimed Skillshots", "Point-and-Click", "Auto-Attack Based"] = _choice("Mechanical demand")
    kit_complexity: Literal["Low", "Medium", "High"] = _choice("Kit complexity")
    power_curve: Literal["Early", "Even", "Late"] = _choice("Power curve")
    snowball_dependence: Literal["Needs a Lead", "Neutral", "Can Play From Behind"] = _choice("Snowball dependence")
    team_dependence: Literal["Self-Sufficient", "Balanced", "Team-Reliant"] = _choice("Team dependence")
    difficulty: Literal["Easy", "Medium", "Hard"] = _choice("Difficulty")
    skill_floor: int = Field(ge=1, le=5, json_schema_extra={"label": "Skill floor", "group": "Gameplay", "hint": "1 to 5. How hard it is to start playing."})
    skill_ceiling: int = Field(ge=1, le=5, json_schema_extra={"label": "Skill ceiling", "group": "Gameplay", "hint": "1 to 5. How far skill can take it. Not below the floor."})
    attack_type: Literal["Melee", "Ranged"] = _choice("Attack type")
    damage_type: Literal["AD", "AP", "Mixed", "Pure"] = _choice("Damage type")
    damage_source: Literal["Abilities", "Auto-Attacks"] = _choice("Damage source")

    @model_validator(mode="after")
    def ceiling_not_below_floor(self):
        if self.skill_ceiling < self.skill_floor:
            raise ValueError("skill_ceiling cannot be lower than skill_floor")
        return self

    @model_validator(mode="after")
    def no_path_tricks_in_image(self):
        if self.image and (".." in self.image):
            raise ValueError("image cannot contain '..'")
        return self


def describe_form(model: type[BaseModel] = CharacterCreate) -> list[dict]:
    """Describes every field of a schema for the website's form builder.

    The form is generated from this, so the schema stays the only place the fields are listed.
    """
    fields = []
    for name, info in model.model_fields.items():
        annotation = info.annotation
        if get_origin(annotation) is Optional or type(None) in get_args(annotation):
            args = [a for a in get_args(annotation) if a is not type(None)]
            annotation = args[0] if args else annotation
        extra = info.json_schema_extra or {}
        options = list(get_args(annotation)) if get_origin(annotation) is Literal else None
        meta = {m.__class__.__name__: m for m in info.metadata}
        field = {
            "name": name,
            "label": extra.get("label", name.replace("_", " ").capitalize()),
            "group": extra.get("group", "Other"),
            "required": info.is_required(),
            "type": "integer" if annotation is int else "string",
            "widget": extra.get("widget") or ("select" if options else "textarea" if extra.get("textarea") else "number" if annotation is int else "text"),
            "options": options,
            "hint": extra.get("hint"),
            "example": extra.get("example"),
        }
        for m in info.metadata:
            for attr, key in (("ge", "min"), ("le", "max"), ("max_length", "max_length"), ("min_length", "min_length")):
                if hasattr(m, attr) and getattr(m, attr) is not None:
                    field[key] = getattr(m, attr)
        fields.append(field)
    return fields
