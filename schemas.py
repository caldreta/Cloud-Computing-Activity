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