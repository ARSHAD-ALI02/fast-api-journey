from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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

class Post(BaseModel):
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"
    
@app.post("/posts")
def create_post(post: Post):
    return {**post.model_dump(), "id": 1} 
