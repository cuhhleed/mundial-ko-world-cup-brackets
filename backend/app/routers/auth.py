from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.auth.verifier import GoogleJwtVerifier, InvalidTokenError, get_verifier
from app.db.cache import update_leaderboard
from app.logging import get_logger
from app.models.bracket import Bracket, SlotPrediction
from app.models.user import UserRecord
from app.services import brackets, users
from app.services.brackets import BracketValidationError, DuplicateBracketError
from app.services.users import UserAlreadyExistsError

logger = get_logger("auth_router")

router = APIRouter(prefix="/api/auth")


class CheckRequest(BaseModel):
    token: str


class CheckResponse(BaseModel):
    exists: bool


class SignupRequest(BaseModel):
    token: str
    predictions: dict[str, SlotPrediction]


class SignupResponse(BaseModel):
    user: UserRecord
    bracket: Bracket


@router.post("/check", response_model=CheckResponse)
def check_user(
    body: CheckRequest,
    verifier: GoogleJwtVerifier = Depends(get_verifier),
) -> CheckResponse:
    try:
        claims = verifier.verify(body.token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = users.get(claims["sub"])
    return CheckResponse(exists=user is not None)


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(
    body: SignupRequest,
    background_tasks: BackgroundTasks,
    verifier: GoogleJwtVerifier = Depends(get_verifier),
) -> SignupResponse:
    try:
        claims = verifier.verify(body.token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user_id = claims["sub"]
    email = claims["email"]

    try:
        user_record = users.create(user_id, email)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already registered.")

    try:
        bracket = brackets.create_bracket(user_id, body.predictions)
    except BracketValidationError as e:
        users.delete(user_id)
        raise HTTPException(status_code=400, detail=e.errors)
    except DuplicateBracketError:
        raise HTTPException(status_code=409, detail="User already has a bracket.")

    background_tasks.add_task(update_leaderboard, user_id, 0)
    logger.info("signup_complete", user_id=user_id, bracket_id=bracket.bracket_id)
    return SignupResponse(user=user_record, bracket=bracket)
