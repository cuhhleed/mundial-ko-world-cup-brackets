from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_user
from app.models.user import (
    AuthenticatedUser,
    UpdateDisplayNameRequest,
    UserRecord,
)
from app.services import users

router = APIRouter(prefix="/api/users")


@router.get("/me", response_model=UserRecord)
def get_me(user: AuthenticatedUser = Depends(require_user)) -> UserRecord | None:
    return users.get(user.user_id)


@router.patch("/me", response_model=UserRecord)
def patch_me(
    body: UpdateDisplayNameRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> UserRecord:
    updated = users.update_display_name(user.user_id, body.display_name)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated
