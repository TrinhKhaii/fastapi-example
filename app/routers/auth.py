from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session

from .. import schemas
from ..database import  get_db
from app.schemas import UserLogin
from .. import models, utils, oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from typing import Annotated

router = APIRouter(tags=['Authentication'])

@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    #  OAuth2PasswordRequestForm
    # {
    #     username: "asdf",
    #     password: "asdfgasd"
    # }
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    

    # create a token
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    #return token
    return {"access_token": access_token, "token_type": "bearer"}
