from pydantic import BaseModel, ConfigDict, EmailStr


class ProjectMemberInviteRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    email: EmailStr