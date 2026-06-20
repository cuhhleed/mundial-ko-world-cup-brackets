from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import require_user
from app.models.bracket import Bracket, BracketTemplate, SlotPrediction
from app.models.user import AuthenticatedUser
from app.services import brackets
from app.services.brackets import BracketValidationError, DuplicateBracketError

router = APIRouter(prefix="/api/brackets")


class BracketCreateRequest(BaseModel):
    predictions: dict[str, SlotPrediction]


@router.post("", response_model=Bracket, status_code=201)
def create_bracket(
    body: BracketCreateRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> Bracket:
    try:
        return brackets.create_bracket(user.user_id, body.predictions)
    except BracketValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)
    except DuplicateBracketError:
        raise HTTPException(status_code=409, detail="User already has a bracket")


@router.get("/template", response_model=BracketTemplate)
def get_bracket_template(
    user: AuthenticatedUser = Depends(require_user),
) -> BracketTemplate:
    return brackets.get_bracket_template()
