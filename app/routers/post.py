from typing import List, Optional
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..utils import hash
from app.schemas import PostCreate, PostOut, PostResponse, UserResponse
from .. import models, oauth2
from ..database import engine, get_db

router = APIRouter(
    prefix="/post",
    tags=['Post']
)


@router.get("/", response_model=List[PostOut])
async def get_all(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),
                   limit: int = 10, skip: int = 0, search: Optional[str] = ""):
   
    # posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()

    # results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).outerjoin(
    #         models.Vote, models.Vote.post_id == models.Post.id).group_by(models.Post.id).all()
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
                    models.Vote, models.Vote.post_id == models.Post.id, 
                    isouter=True).group_by(models.Post.id).filter(
                    models.Post.title.contains(search)).offset(skip).limit(limit).all()
   

    return results


@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def add_data(post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""",
    #                (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()

    # new_post = models.Post(title=post.title, content=post.content, published=post.published)
    
    new_post = models.Post(owner_id=current_user.id, **post.__dict__)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/get/{id}", response_model=PostOut)
async def get_data(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(id), )) # để dấu phẩy ở đây để phòng trường hợp bị lỗi sẽ được xử lý
    # post = cursor.fetchone()
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
                    models.Vote, models.Vote.post_id == models.Post.id, 
                    isouter=True).group_by(models.Post.id).filter(models.Post.id == id).first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found post with id {id}")
    
    if post.Post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform request action")
    
    return post


@router.delete("/delete/{id}")
async def delete_data(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    # deleted_post = cursor.fetchone()
    # conn.commit()
    deleted_post_query = db.query(models.Post).filter(models.Post.id == id)
    deleted_post = deleted_post_query.first()

    if deleted_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found data with id {id}")
    
    if deleted_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform request action")

    deleted_post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    

@router.put("/update/{id}", response_model=PostResponse)
async def update_data(id: int, updated_post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""UPDATE posts SET title = %s, content = %s, published =  %s WHERE ID = %s RETURNING *""",
    #                (post.title, post.content, post.published, str(id)))
    # updated_post = cursor.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)

    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} does not exist")
    
    if post_query.first().owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform request action")
    
    post_query.update(updated_post.__dict__, synchronize_session=False)
    db.commit()
    return post_query.first()