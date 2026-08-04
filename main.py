from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from fastapi import HTTPException


app = FastAPI()

#------------------------------------------------
#Lesson 1 & 2 

@app.get("/")
def read_root():
    return {"message" : "Welcome! Arshad"}

@app.get("/posts")
def get_posts(status: str = "draft"):
    return {"status" : status, "message" : "Fetching Request Status"}

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"post_id" : post_id, "message" :  "Fetching Request Post"}

@app.get("/users/{username}/posts")
def get_user_info(username: str):
    return {"username" : username, "total_posts" : 0}

class PostIn(BaseModel):
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"
    
@app.post("/posts")
def create_post(post: PostIn):
    return {**post.model_dump(), "id": 1} 

#-----------------------------------------
#Lesson 3

DATABASE_URL = "sqlite:///./posts.db"
engine = create_engine(DATABASE_URL)

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def create_tables():
    SQLModel.metadata.create_all(engine)

@app.get("/posts")
def get_posts(session: Session = Depends(get_session)):
    return session.exec(select(Post)).all()

@app.post("/posts")
def create_post(post: Post, session: Session = Depends(get_session)):
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

#----------------------------------------------------------------
#lesson # 4
@app.delete("/posts/{post_id}")
def delete_post(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code= 404, detail="Post Not Found")
    session.delete(post)
    session.commit()
    return {"message": "Succesfully Deleted"}

@app.put("/posts/{post_id}")
def update_post(post_id: int, updated: Post, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")
    post.title    = updated.title
    post.content  = updated.content
    post.status   = updated.status
    post.platform = updated.platform
    session.commit()
    session.refresh(post)
    return {"message" : "Updated Succesfully"}