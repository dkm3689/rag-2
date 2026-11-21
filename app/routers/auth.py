from fastapi import APIRouter, Depends, HTTPException

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.security import hash_password, create_access_token, verify_password

from app.schemas import UserOut, UserCreate, Token
from app.models import User

from app.database import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=201, response_model=UserOut)
def signup(user_in: UserCreate, db:Session = Depends(get_db) ):
    existing = db.query(User).filter(User.email == user_in.email ).first()
    print("Existing", existing)
    print("User in", user_in)
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form.username).first()
    print("User", user)
    if user is None or not verify_password( form.password, user.hashed_password ):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers = {"WWW-Authenticate": "Bearer"} )
    
    return Token(access_token=create_access_token(user.id) ,token_type="bearer")