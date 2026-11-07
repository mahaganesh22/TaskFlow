from uuid import UUID

from pydantic import BaseModel


class TransferOwnershipRequest(BaseModel):
    new_owner_id: UUID