from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import require_user
from app.models.bracket import Bracket, BracketResponse, BracketTemplate, SlotPrediction
from app.models.user import AuthenticatedUser
from app.services import brackets, users
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
def get_bracket_template() -> BracketTemplate:
    return brackets.get_bracket_template()


@router.get("/me", response_model=BracketResponse)
def get_my_bracket(
    user: AuthenticatedUser = Depends(require_user),
) -> BracketResponse:
    user_record = users.get(user.user_id)
    if user_record is None or user_record.bracket_id is None:
        raise HTTPException(status_code=404, detail="No bracket found for user")
    bracket = brackets.get_bracket(user_record.bracket_id)
    if bracket is None:
        raise HTTPException(status_code=404, detail="Bracket not found")
    return brackets.build_bracket_response(bracket)


@router.get("/{bracket_id}", response_model=BracketResponse)
def get_bracket(bracket_id: str) -> BracketResponse:
    bracket = brackets.get_bracket(bracket_id)
    if bracket is None:
        raise HTTPException(status_code=404, detail="Bracket not found")
    return brackets.build_bracket_response(bracket)
