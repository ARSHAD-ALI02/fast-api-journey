"""
main.py — FastAPI Posts API

A small REST API for managing social-media posts (drafts queue for
LinkedIn, Twitter, etc.), with user registration, login, and JWT-protected
create. Backed by SQLite via SQLModel.

Lesson map:
    1. In-memory endpoints
    2. Pydantic request model  (folded into the SQLModel below)
    3. SQLModel + SQLite
    4. Update & Delete
    5. Auth: register, login, JWT-protected POST /posts
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm


from auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
)

def fake_publish_to_linkedin(post_id: int, title: str):
    import time
    time.sleep(3)   # simulates a slow external API call
    print(f"Post {post_id} '{title}' published to LinkedIn!")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="FastAPI Posts API", version="1.0.0")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./posts.db"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    """FastAPI dependency that yields a fresh DB session per request."""
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def create_tables() -> None:
    """Create all SQLModel tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hashed_password: str


# ---------------------------------------------------------------------------
# Lesson 1 — basic / in-memory endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    """Health-check / welcome endpoint."""
    return {"message": "Welcome! Arshad"}


@app.get("/users/{username}/posts")
def get_user_info(username: str):
    """Sample user-scoped route (in-memory, no DB)."""
    return {"username": username, "total_posts": 0}


# ---------------------------------------------------------------------------
# Lesson 5 — Auth
# ---------------------------------------------------------------------------
@app.post("/register")
def register(
    username: str,
    password: str,
    session: Session = Depends(get_session),
):
    """Register a new user with a bcrypt-hashed password."""
    if session.exec(select(User).where(User.username == username)).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User created", "id": user.id}



@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Lesson 3 & 4 — Post CRUD
# ---------------------------------------------------------------------------
@app.get("/posts")
def list_posts(session: Session = Depends(get_session)):
    """Return all posts from the database."""
    return session.exec(select(Post)).all()


@app.post("/posts", status_code=201)
def create_post(
    post: Post,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user),  # protected
):
    """Create a new post. Requires a valid JWT."""
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@app.put("/posts/{post_id}")
def update_post(
    post_id: int,
    updated: Post,
    session: Session = Depends(get_session),
):
    """Replace a post's fields. 404 if the id doesn't exist."""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")

    post.title = updated.title
    post.content = updated.content
    post.status = updated.status
    post.platform = updated.platform

    session.commit()
    session.refresh(post)
    return {"message": "Updated Successfully", "post": post}


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, session: Session = Depends(get_session)):
    """Delete a post by id. 404 if it doesn't exist."""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")

    session.delete(post)
    session.commit()
    return {"message": "Successfully Deleted"}

@app.post("/posts/{post_id}/publish")
def publish_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user)
):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = "Published"
    session.commit()
    
    background_tasks.add_task(fake_publish_to_linkedin, post.id, post.title)
    
    return {"message": f"Post {post_id} is being published", "status": "processing"}