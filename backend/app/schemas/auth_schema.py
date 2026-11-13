from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from uuid import UUID

class UserPublicResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class UserProfileResponse(UserPublicResponse):
    education: str | None = None
    skills: str | None = None
    projects: str | None = None
    experience: str | None = None


class UserProfileUpdateRequest(BaseModel):
    education: str | None = Field(default=None, max_length=4000)
    skills: str | None = Field(default=None, max_length=4000)
    projects: str | None = Field(default=None, max_length=6000)
    experience: str | None = Field(default=None, max_length=6000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("education", "skills", "projects", "experience")
    @classmethod
    def normalize_profile_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    education: str | None = Field(default=None, max_length=4000)
    skills: str | None = Field(default=None, max_length=4000)
    projects: str | None = Field(default=None, max_length=6000)
    experience: str | None = Field(default=None, max_length=6000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain an uppercase letter")

        if not any(char.islower() for char in value):
            raise ValueError("Password must contain a lowercase letter")

        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain a digit")

        return value

    @field_validator("education", "skills", "projects", "experience")
    @classmethod
    def normalize_profile_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserPublicResponse"


from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)
