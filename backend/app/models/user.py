from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str


class UserRecord(BaseModel):
    user_id: str
    email: str
    display_name: str
    bracket_id: str | None = None
    created_at: str
