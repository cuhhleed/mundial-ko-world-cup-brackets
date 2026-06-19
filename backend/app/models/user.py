from typing import Annotated

from pydantic import BaseModel, StringConstraints


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str


class UpdateDisplayNameRequest(BaseModel):
    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=3,
            max_length=30,
            pattern=r"^[A-Za-z0-9 ]+$",
        ),
    ]


class UserRecord(BaseModel):
    user_id: str
    email: str
    display_name: str
    bracket_id: str | None = None
    created_at: str
