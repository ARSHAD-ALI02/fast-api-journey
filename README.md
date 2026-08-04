# FastAPI Posts API

A small RESTful API for managing **social media posts** (think: a "drafts" queue for LinkedIn, Twitter, etc.), built with **FastAPI** and **SQLModel**, backed by a local **SQLite** database.

> **Note:** This project uses **FastAPI**, not Flask. They are both popular Python web frameworks, but they are different:
>
> | Feature | Flask | FastAPI (this project) |
> |---|---|---|
> | Async support | Limited (via extensions) | Built-in (`async`/`await`) |
> | Data validation | Manual / via extensions | Automatic via **Pydantic** |
> | API docs | Manual (e.g. Flask-RESTX) | **Auto-generated** at `/docs` (Swagger UI) and `/redoc` |
> | Type hints | Optional | First-class — request/response models use Python type hints |
> | Performance | Good | Very fast (on par with Node.js / Go) |
> | Standards | WSGI | ASGI |

If you're looking for a Flask-style experience, FastAPI will feel familiar but faster and more "type-driven."

---

## What This API Does

It is a CRUD API for `Post` objects with the following fields:

- `id` *(int, auto-generated)* — primary key
- `title` *(string, required)*
- `content` *(string, required)*
- `status` *(string, default `"Draft"`)*
- `platform` *(string, default `"LinkedIn"`)*

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Welcome message |
| `GET` | `/posts?status=...` | List posts (filtered by status, in-memory — Lesson 1) |
| `GET` | `/posts/{post_id}` | Echo a single post id (in-memory — Lesson 1) |
| `GET` | `/users/{username}/posts` | Echo a user's post count (in-memory — Lesson 1) |
| `POST` | `/posts` | Create a post (Pydantic-only — Lesson 2 / DB version in Lesson 3) |
| `GET` | `/posts` | List all posts from the database (Lesson 3) |
| `POST` | `/posts` | Create a post and save it to the database (Lesson 3) |
| `PUT` | `/posts/{post_id}` | Update a post in the database (Lesson 4) |
| `DELETE` | `/posts/{post_id}` | Delete a post from the database (Lesson 4) |

Once the server is running, you can browse the **interactive Swagger docs** at:

```
http://127.0.0.1:8000/docs
```

---

## How to Run

```bash
# 1. (Optional but recommended) Create & activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server (with auto-reload during development)
uvicorn main:app --reload
```

Then visit:

- `http://127.0.0.1:8000/` — welcome message
- `http://127.0.0.1:8000/docs` — interactive API documentation (Swagger UI)
- `http://127.0.0.1:8000/redoc` — alternative API documentation (ReDoc)

The SQLite database file `posts.db` is created automatically on first start.

---

## Walkthrough of `main.py`

Below is a section-by-section explanation of the code.

### 1. Imports

```python
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from fastapi import HTTPException
```

- `FastAPI` — the main application class.
- `Depends` — FastAPI's dependency-injection helper (used to hand the DB session to each route).
- `SQLModel`, `Field`, `Session`, `create_engine`, `select` — SQLModel combines SQLAlchemy + Pydantic. We use it to define our DB model **and** its validation in a single class.
- `Optional[int]` — used to declare an auto-incrementing primary key that can be `None` until the row is saved.
- `HTTPException` — used to return proper HTTP error responses (e.g. 404).

> **Heads-up:** `BaseModel` is referenced later in the file (for the Pydantic-only `Post` in Lesson 2) but is **not imported**. If you only want the Lesson 2 behavior, add `from pydantic import BaseModel` to the top.

### 2. App instance

```python
app = FastAPI()
```

Creates the ASGI application. `uvicorn main:app` loads this object to serve HTTP traffic.

### 3. Lesson 1 — In-memory endpoints

These are simple, no-database routes used to learn how URL parameters, query parameters, and path parameters work in FastAPI.

```python
@app.get("/")
def read_root():
    return {"message": "Welcome! Arshad"}
```

- `GET /` — returns a JSON welcome message.

```python
@app.get("/posts")
def get_posts(status: str = "draft"):
    return {"status": status, "message": "Fetching Request Status"}
```

- `GET /posts` — accepts an optional **query parameter** `status` (defaults to `"draft"`) and echoes it back.

```python
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"post_id": post_id, "message": "Fetching Request Post"}
```

- `GET /posts/{post_id}` — `post_id` is automatically converted to `int`. If the URL has a non-integer (e.g. `/posts/abc`), FastAPI returns a 422 validation error automatically.

```python
@app.get("/users/{username}/posts")
def get_user_info(username: str):
    return {"username": username, "total_posts": 0}
```

- `GET /users/{username}/posts` — a sample "user-scoped" route showing how to capture path parameters.

### 4. Lesson 2 — Pydantic request model

```python
class Post(BaseModel):
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"

@app.post("/posts")
def create_post(post: Post):
    return {**post.model_dump(), "id": 1}
```

- The first `Post` class is a **Pydantic** model (this is what Lesson 2 is about). It describes the *shape* of incoming JSON.
- `title` and `content` are required; `status` and `platform` have defaults.
- `post.model_dump()` converts the Pydantic object back to a dict, then we add a fake `id`. **Note:** nothing is actually saved yet — this is a Pydantic-only lesson.

> ⚠️ Because `Post` is **redefined** further down as a `SQLModel`, the second definition overwrites the first. In practice, only the database-backed routes (`Lesson 3`/`4`) will work end-to-end. To keep both behaviors, rename one of them (e.g. `PostIn` for the Pydantic input model).

### 5. Lesson 3 — Database with SQLModel + SQLite

```python
DATABASE_URL = "sqlite:///./posts.db"
engine = create_engine(DATABASE_URL)
```

- `sqlite:///./posts.db` means "SQLite database file named `posts.db` in the current directory."
- `create_engine` creates the SQLAlchemy engine that manages the connection pool.

```python
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    status: str = "Draft"
    platform: str = "LinkedIn"
```

- `Post` is now both a **Pydantic model** (request/response validation) **and** a **SQLAlchemy table** (`table=True`).
- `Field(default=None, primary_key=True)` makes `id` an auto-incrementing primary key.

```python
def get_session():
    with Session(engine) as session:
        yield session
```

- A FastAPI **dependency** that yields a fresh DB session per request and closes it when the request finishes.

```python
@app.on_event("startup")
def create_tables():
    SQLModel.metadata.create_all(engine)
```

- On app startup, this creates all tables defined by `SQLModel` subclasses (i.e. the `Post` table) if they don't already exist.

```python
@app.get("/posts")
def get_posts(session: Session = Depends(get_session)):
    return session.exec(select(Post)).all()
```

- `select(Post)` builds a `SELECT * FROM post` query.
- `session.exec(...).all()` runs the query and returns all rows as `Post` objects.

```python
@app.post("/posts")
def create_post(post: Post, session: Session = Depends(get_session)):
    session.add(post)
    session.commit()
    session.refresh(post)
    return post
```

- Adds the new `Post` to the session, commits the transaction, refreshes it (to pull DB-generated fields like `id` back into the object), and returns it as JSON.

### 6. Lesson 4 — Update & Delete

```python
@app.delete("/posts/{post_id}")
def delete_post(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")
    session.delete(post)
    session.commit()
    return {"message": "Successfully Deleted"}
```

- `session.get(Post, post_id)` fetches by primary key.
- If the post doesn't exist, raise a 404 with a clear error message.
- Otherwise, delete and commit.

```python
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
    return {"message": "Updated Successfully"}
```

- Fetch the existing row, copy each field from the incoming payload, and commit.
- For a more idiomatic PATCH-style update you could use `updated.model_dump(exclude_unset=True)`, but this explicit field-by-field copy is easy to read and keeps the lesson focused.

---

## Example Requests

Using `curl`:

```bash
# Create a post
curl -X POST http://127.0.0.1:8000/posts \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Hello LinkedIn\",\"content\":\"First post!\",\"status\":\"Draft\",\"platform\":\"LinkedIn\"}"

# List all posts
curl http://127.0.0.1:8000/posts

# Update post 1
curl -X PUT http://127.0.0.1:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Updated Title\",\"content\":\"Updated content\",\"status\":\"Published\",\"platform\":\"LinkedIn\"}"

# Delete post 1
curl -X DELETE http://127.0.0.1:8000/posts/1
```

Or just use the auto-generated docs at `http://127.0.0.1:8000/docs` — they let you click and test every endpoint from your browser.

---

## Project Structure

```
FastAPI framework/
├── main.py            # All the routes and DB model (this file's subject)
├── requirements.txt   # Python dependencies
├── README.md          # You are here
├── posts.db           # Auto-created SQLite database (after first run)
└── venv/              # Local virtual environment (you create this)
```

---

## Possible Next Steps

- Split routes into separate modules (e.g. `routers/posts.py`).
- Add user authentication (e.g. OAuth2 with `fastapi-users`).
- Add pagination and filtering on `GET /posts`.
- Switch the DB to PostgreSQL by changing `DATABASE_URL`.
- Add Alembic for proper database migrations.
- Add automated tests with **pytest** and FastAPI's `TestClient`.
