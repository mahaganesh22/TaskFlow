from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreateRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Comment cannot be empty")

        return value