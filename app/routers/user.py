from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..utils import hash
from app.schemas import  UserCreate, UserResponse
from .. import models
from ..database import engine, get_db


router = APIRouter(
    prefix="/user",
    tags=['User']
)

@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def add_data(user: UserCreate, db: Session = Depends(get_db)):
    user.password = hash(user.password)
    
    new_user = models.User(**user.__dict__)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} does not exist")
    
    return user