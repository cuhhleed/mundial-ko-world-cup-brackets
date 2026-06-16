from fastapi import APIRouter, Depends

from app.auth.dependencies import require_user
from app.models.user import AuthenticatedUser, UserRecord
from app.services import users

router = APIRouter(prefix="/api/users")


@router.get("/me", response_model=UserRecord)
def get_me(user: AuthenticatedUser = Depends(require_user)) -> UserRecord | None:
    return users.get(user.user_id)
